import logging
from types import SimpleNamespace
from typing import Any, Dict

from canvases.models import CanvasNodeRelation, ConceptualEdge, ConceptualNode
from canvases.serializers import ConceptualGraphSerializer
from canvases.utils import (create_new_canvas_by_workflow_id,
                            create_or_update_conceptual_edges,
                            create_or_update_conceptual_node_relations,
                            get_conceptual_graph)
from core.celery_app import celery_app
from core.constants import EntityStatus
from messaging.constants import (AgentRequest, CreateNewCanvas,
                                 GetRecommendedConceptualNodes,
                                 RecommendConceptualNodes)
from messaging.tasks import publish_event
from realtime.constants import CONCEPTUAL_NODES_RECOMMENDATION
from realtime.utils import send_ws_notification

logger = logging.getLogger(__name__)

@celery_app.task(name=CreateNewCanvas.name, ignore_result=True)
def create_new_canvas(event_type: str, payload: dict):
    task_id = create_new_canvas.request.id
    workflow_id = payload.get('workflow_id')
    if workflow_id is None:
        logger.error('Task %s: workflow_id can not be None.', task_id)
        raise ValueError('workflow_id can not be None.')

    create_new_canvas_by_workflow_id(workflow_id)

    logger.info("Task %s: a new canvas was created for workflow %s.", task_id, workflow_id)


@celery_app.task(name=GetRecommendedConceptualNodes.name, ignore_result=True)
def get_recommended_conceptual_nodes(event_type: str, payload: dict):
    task_id = get_recommended_conceptual_nodes.request.id

    user_id = payload.get('user_id', '')
    canvas_id = payload.get('canvas_id', '')

    method = payload.get('method', 'get')
    if method == 'create_or_update':
        conceptual_graph: Dict[str, Any] = payload.get('agent_output', {})
        create_or_update_conceptual_node_relations(
            canvas_id=canvas_id,
            data=conceptual_graph.get('nodes', {})
        )
        create_or_update_conceptual_edges(
            canvas_id=canvas_id,
            data=conceptual_graph.get('edges', [])
        )

    modified_conceptual_graph = get_conceptual_graph(canvas_id)

    send_ws_notification(
        user_id=user_id,
        event_type=CONCEPTUAL_NODES_RECOMMENDATION,
        payload=dict(modified_conceptual_graph)
    )

@celery_app.task(name=RecommendConceptualNodes.name, ignore_result=True)
def handle_recommend_conceptual_nodes_request(event_type: str, payload: dict):
    task_id = handle_recommend_conceptual_nodes_request.request.id

    user_id = payload.get('user_id', '')
    workflow_id = payload.get('workflow_id', '')
    canvas_id = payload.get('canvas_id', '')

    canvas_node_relations = CanvasNodeRelation.objects.filter(canvas__id=canvas_id).all()
    recommended_nodes = [relation for relation in canvas_node_relations if relation.status == EntityStatus.AI_EXTRACTED]
    if recommended_nodes:
        publish_event.delay(
            event_type=GetRecommendedConceptualNodes.name,
            payload={
                'user_id': user_id,
                'canvas_id': canvas_id,
                'method': 'get'
            },
            queue=GetRecommendedConceptualNodes.queue
        )
        return

    on_pool_nodes = ConceptualNode.objects.filter(workflow__workflow_id=workflow_id).exclude(canvases__id=canvas_id).distinct()

    on_canvas_str = "\n".join([f"- [{relation.node.node_type}] {relation.node.label} (ID: {relation.node.id})" for relation in canvas_node_relations])
    pool_str = "\n".join([f"- [{node.node_type}] {node.label} (ID: {node.id})" for node in on_pool_nodes])

    on_canvas_edges = ConceptualEdge.objects.filter(canvas__id=canvas_id).all()

    graph_instance = SimpleNamespace(
        nodes={relation.node.id: relation.node for relation in canvas_node_relations},
        edges=on_canvas_edges
    )
    conceptual_graph_serializer = ConceptualGraphSerializer(graph_instance)

    payload = {
        'agent_role_name': 'GraphSynthesistAgent',
        'agent_input_data': {
            'on_canvas_str': on_canvas_str if 'FOCUS' in on_canvas_str else "EMPTY - Create initial FOCUS.",
            'pool_str': pool_str
        },
        'tool_args_map': {'spatial_locate': {'existing_graph_state': conceptual_graph_serializer.data}},
        'next_event_type': GetRecommendedConceptualNodes.name,
        'next_event_payload': {
            'user_id': user_id,
            'canvas_id': canvas_id,
            'method': 'create_or_update'
        },
        'next_event_queue': GetRecommendedConceptualNodes.queue,
    }

    publish_event.delay(
        event_type=AgentRequest.name,
        payload=payload,
        queue=AgentRequest.queue
    )
