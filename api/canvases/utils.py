import logging
from types import SimpleNamespace
from typing import Any, Dict
from uuid import UUID

from canvases.models import (CanvasNodeRelation, ConceptualCanvas,
                             ConceptualEdge, ConceptualNode)
from canvases.serializers import (ConceptualGraphSerializer,
                                  ConceptualNodeSerializer)
from core.constants import EntityStatus
from django.apps import apps
from django.db import transaction
from django.db.models import Q

logger = logging.getLogger(__name__)


def create_new_canvas_by_workflow_id(workflow_id: UUID):
    ResearchWorkflow = apps.get_model('workflows', 'ResearchWorkflow')
    ExplorationPhaseData = apps.get_model('workflows', 'ExplorationPhaseData')
    try:
        workflow = ResearchWorkflow.objects.get(workflow_id=workflow_id)
    except ResearchWorkflow.DoesNotExist:
        logger.error("Workflow with id %s does not exist. Cannot create canvas.", workflow_id)
        return

    canvas = ConceptualCanvas.objects.filter(workflow=workflow)

    if canvas.exists():
        logger.warning("Workflow %s already has a canvas. Skipping creation.", workflow_id)
        return

    canvas = ConceptualCanvas(name='Default Canvas', workflow=workflow)
    canvas.save()

    exploration_phase_data = ExplorationPhaseData.objects.get(workflow=workflow)
    setattr(exploration_phase_data, 'activated_canvas_id', canvas.id)
    exploration_phase_data.save()

    node = ConceptualNode(label=canvas.name, node_type='NAVIGATION')
    canvas.navigator.add(node, bulk=False)

    return canvas

def create_or_update_conceptual_edges(canvas_id: str, data):
    conceptual_edges = ConceptualEdge.objects.filter(canvas_id=canvas_id).all()
    on_canvas_edges = {f'{edge.source}_{edge.target}': edge for edge in conceptual_edges}

    instances = []
    for edge in data:
        statement = (
            (f'{edge['source']}_{edge['target']}' not in on_canvas_edges)
            and (f'{edge['target']}_{edge['source']}' not in on_canvas_edges)
        )
        if statement:
            instances.append(ConceptualEdge(
                source=edge['source'],
                source_handle=edge['source_handle'],
                target=edge['target'],
                target_handle=edge['target_handle'],
                weight=edge['weight'],
                canvas_id=canvas_id
            ))

    ConceptualEdge.objects.bulk_create(instances)

def create_or_update_conceptual_node_relations(canvas_id: str, data: Dict[str, Any]):
    relation_instances = CanvasNodeRelation.objects.filter(canvas__id=canvas_id).all()
    on_canvas_nodes = {str(relation.node.id): relation for relation in relation_instances}

    instances = []
    for node_id, node in data.items():
        if node_id in on_canvas_nodes:
            relation = on_canvas_nodes[node_id]
            relation.x = node['position'].get('x')
            relation.y = node['position'].get('y')
        else:
            relation = CanvasNodeRelation(
                canvas_id=canvas_id,
                node_id=node_id,
                x=node['position'].get('x'),
                y=node['position'].get('y'),
                rationale=node.get('rationale'),
                status=EntityStatus.AI_EXTRACTED
            )

        instances.append(relation)

    CanvasNodeRelation.objects.bulk_create(instances, ignore_conflicts=True)

def get_conceptual_graph(canvas_id: str):
    canvas_node_relations = CanvasNodeRelation.objects.filter(canvas__id=canvas_id).all()
    on_canvas_edges = ConceptualEdge.objects.filter(canvas__id=canvas_id).all()
    on_graph_nodes = {}
    for relation in canvas_node_relations:
        node = set_position_to_relation_nodes(relation)
        on_graph_nodes[node.id] = node

    graph_instance = SimpleNamespace(
        nodes={relation.node.id: relation.node for relation in canvas_node_relations},
        edges=on_canvas_edges
    )
    conceptual_graph_serializer = ConceptualGraphSerializer(graph_instance)
    return conceptual_graph_serializer.data

def delete_canvas_node_relation_by_constraint(canvas_id: str, node_id: str):
    instance = CanvasNodeRelation.objects.get(canvas_id=canvas_id, node_id=node_id)
    if not instance:
        return

    with transaction.atomic():
        ConceptualEdge.objects.filter(
            Q (canvas_id=canvas_id) & (Q(source=node_id) | Q(target=node_id))
        ).delete()
        instance.delete()

def set_position_to_relation_nodes(relation: CanvasNodeRelation):
    position = SimpleNamespace(
        x=relation.x,
        y=relation.y
    )
    setattr(relation.node, 'position', position)
    setattr(relation.node, 'status', relation.status)
    return relation.node

def update_canvas_node_relation_by_constraint(canvas_id: str, node_id: str, data: Dict[str, Any]):
    instance = CanvasNodeRelation.objects.get(canvas_id=canvas_id, node_id=node_id)
    for key, value in data.items():
        if value is None or key in ['id']:
            continue

        if key == 'position':
            instance.x = value['x']
            instance.y = value['y']

        setattr(instance, key, value)

    instance.save()

    node = set_position_to_relation_nodes(instance)
    serializer = ConceptualNodeSerializer(node)
    return serializer.data
