import logging
from types import SimpleNamespace
from typing import Any, Dict
from uuid import uuid4

from canvases.models import CanvasNodeRelation, ConceptualEdge, ConceptualNode
from canvases.serializers import ConceptualGraphSerializer
from canvases.utils import (create_new_canvas_by_project_id,
                            create_or_update_conceptual_edges,
                            create_or_update_conceptual_node_relations,
                            get_conceptual_graph)
from core.celery_app import celery_app
from core.constants import EntityStatus
from messaging.constants import (AgentRequest, CreateNewCanvas,
                                 GetRecommendedConceptualEdges,
                                 GetRecommendedConceptualNodes,
                                 RecommendConceptualEdges,
                                 RecommendConceptualNodes)
from messaging.tasks import publish_event
from realtime.constants import (CONCEPTUAL_EDGES_RECOMMENDATION,
                                CONCEPTUAL_NODES_RECOMMENDATION)
from realtime.utils import send_ws_notification

logger = logging.getLogger(__name__)

@celery_app.task(name=CreateNewCanvas.name, ignore_result=True)
def create_new_canvas(event_type: str, payload: dict):
    task_id = create_new_canvas.request.id
    project_id = payload.get('project_id')
    if project_id is None:
        logger.error('Task %s: project_id can not be None.', task_id)
        raise ValueError('project_id can not be None.')

    create_new_canvas_by_project_id(project_id)

    logger.info("Task %s: a new canvas was created for project %s.", task_id, project_id)


@celery_app.task(name=GetRecommendedConceptualNodes.name, ignore_result=True)
def get_recommended_conceptual_nodes(event_type: str, payload: dict):
    task_id = get_recommended_conceptual_nodes.request.id

    user_id = payload.get('user_id', '')
    canvas_id = payload.get('canvas_id', '')
    newly_onboarded_nodes = payload.get('newly_onboarded_nodes', [])
    recommendation_mode = payload.get('recommendation_mode', '')

    method = payload.get('method', 'get')
    if method == 'create_or_update':
        agent_output: Dict[str, Any] = payload.get('agent_output', {})
        conceptual_nodes = {}
        conceptual_edges = agent_output.get('edges', [])
        for node in newly_onboarded_nodes:
            if node.get('rationale', '') is None:
                node['rationale'] = ''

            conceptual_nodes[node['id']] = node

        for edge in conceptual_edges:
            edge['id'] = str(uuid4())

        create_or_update_conceptual_node_relations(
            canvas_id=canvas_id,
            data=conceptual_nodes
        )
        create_or_update_conceptual_edges(
            canvas_id=canvas_id,
            data=conceptual_edges
        )

    modified_conceptual_graph = get_conceptual_graph(canvas_id)
    if recommendation_mode == 'directed':
        event_type = CONCEPTUAL_NODES_RECOMMENDATION
    elif recommendation_mode == 'autonomous':
        event_type = CONCEPTUAL_EDGES_RECOMMENDATION
    else:
        raise ValueError(f"Invalid recommendation_mode: {recommendation_mode}")

    send_ws_notification(
        user_id=user_id,
        event_type=event_type,
        payload=dict(modified_conceptual_graph)
    )

@celery_app.task(name=RecommendConceptualEdges.name, ignore_result=True)
def handle_recommend_conceptual_edges_request(event_type: str, payload: dict):
    task_id = handle_recommend_conceptual_edges_request.request.id

    user_id = payload.get('user_id', '')
    canvas_id = payload.get('canvas_id', '')
    on_canvas_str = payload.get('on_canvas_str', '')
    on_canvas_ids = payload.get('on_canvas_ids', '')
    newly_onboarded_nodes = payload.get('newly_onboarded_nodes', [])
    recommendation_mode = payload.get('recommendation_mode', '')
    if recommendation_mode == 'directed':
        agent_role_name = 'DirectedWeaverAgent'
        agent_output = payload.get('agent_output', {})
        newly_onboarded_nodes = list(
            node for node in agent_output['nodes'].values()
            if node['id'] not in on_canvas_ids
        )

        newly_onboarded_nodes_str = "\n".join([
            f"- [{node['type']}] {node['label']} (id: {node['id']}, anchor_id: {node['anchor_id']})"
            for node in newly_onboarded_nodes
        ])
    elif recommendation_mode == 'autonomous':
        agent_role_name = 'AutonomousWeaverAgent'
        canvas_node_relations = CanvasNodeRelation.objects.filter(canvas__id=canvas_id, node__status='LOCKED').all()
        on_canvas_str = "\n".join([f"- [{relation.node.node_type}] {relation.node.label} (ID: {relation.node.id})" for relation in canvas_node_relations])
        on_canvas_ids = [str(relation.node.id) for relation in canvas_node_relations]

        newly_onboarded_nodes_str = "\n".join([
            f"- [{node['type']}] {node['label']} (id: {node['id']})"
            for node in newly_onboarded_nodes
        ])
    else:
        raise ValueError(f"Invalid recommendation_mode: {recommendation_mode}")

    payload = {
        'agent_role_name': agent_role_name,
        'agent_input_data': {
            'on_canvas_str': on_canvas_str,
            'newly_onboarded_nodes_str': newly_onboarded_nodes_str
        },
        'next_event_type': GetRecommendedConceptualNodes.name,
        'next_event_payload': {
            'user_id': user_id,
            'canvas_id': canvas_id,
            'recommendation_mode': recommendation_mode,
            'newly_onboarded_nodes': newly_onboarded_nodes,
            'method': 'create_or_update'
        },
        'next_event_queue': GetRecommendedConceptualNodes.queue,
    }

    publish_event.delay(
        event_type=AgentRequest.name,
        payload=payload,
        queue=AgentRequest.queue
    )

@celery_app.task(name=RecommendConceptualNodes.name, ignore_result=True)
def handle_recommend_conceptual_nodes_request(event_type: str, payload: dict):
    task_id = handle_recommend_conceptual_nodes_request.request.id

    user_id = payload.get('user_id', '')
    project_id = payload.get('project_id', '')
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

    on_pool_nodes = ConceptualNode.objects.filter(project__id=project_id).exclude(canvases__id=canvas_id).distinct()

    on_canvas_str = "\n".join([f"- [{relation.node.node_type}] {relation.node.label} (ID: {relation.node.id})" for relation in canvas_node_relations])
    on_canvas_ids = [str(relation.node.id) for relation in canvas_node_relations]
    pool_str = "\n".join([f"- [{node.node_type}] {node.label} (ID: {node.id})" for node in on_pool_nodes])

    on_canvas_edges = ConceptualEdge.objects.filter(
        canvas__id=canvas_id
    ).select_related(
        'source', 'target'
    ).all()

    graph_nodes = {}
    for relation in canvas_node_relations:
        graph_nodes[relation.node.id] = relation

    graph_instance = SimpleNamespace(
        canvas_id=canvas_id,
        nodes=graph_nodes,
        edges=on_canvas_edges
    )
    conceptual_graph_serializer = ConceptualGraphSerializer(graph_instance)

    payload = {
        'agent_role_name': 'GraphSynthesistAgent',
        'agent_input_data': {
            'on_canvas_str': on_canvas_str if on_canvas_str else "EMPTY - Create initial FOCUS.",
            'pool_str': pool_str
        },
        'tool_args_map': {'spatial_locate': {'existing_graph_state': conceptual_graph_serializer.data}},
        'next_event_type': RecommendConceptualEdges.name,
        'next_event_payload': {
            'user_id': user_id,
            'canvas_id': canvas_id,
            'on_canvas_str': on_canvas_str,
            'on_canvas_ids': on_canvas_ids,
            'recommendation_mode': 'directed'
        },
        'next_event_queue': RecommendConceptualEdges.queue,
    }

    publish_event.delay(
        event_type=AgentRequest.name,
        payload=payload,
        queue=AgentRequest.queue
    )
