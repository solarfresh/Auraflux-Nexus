import logging
from types import SimpleNamespace
from uuid import UUID

from canvases.serializers import ConceptualGraphSerializer
from core.constants import EntityStatus
from django.apps import apps
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from messaging.constants import AgentRequest, CreateNewCanvas
from messaging.tasks import publish_event
from workflows.models import ExplorationPhaseData, ResearchWorkflow

logger = logging.getLogger(__name__)

def atomic_read_and_lock_exploration_data(
    workflow_id: UUID,
    user_id: int,
    stability_score: int,
    final_research_question: str
) -> tuple[ResearchWorkflow, ExplorationPhaseData]:
    """
    Executes a single atomic transaction to lock the state and load the exploration data.
    This is the function called by the WorkflowChatInputView.
    """

    # Ensures the entire sequence is locked and atomic
    with transaction.atomic():
        # Retrieve and LOCK the main state
        # Note: Must use select_for_update() for locking
        workflow = get_object_or_404(
            ResearchWorkflow.objects.select_for_update(),
            workflow_id=workflow_id,
            user_id=user_id
        )

        # Retrieve or Create and LOCK the phase data
        # We need to get or create the ExplorationPhaseData instance.
        # Since it is a OneToOne relationship, the lock on the parent often suffices,
        # but select_for_update() is safer if the instance exists.

        logger.debug("call the synchronous helper function *within* the atomic block")
        exploration_data = get_or_create_exploration_data(
            workflow,
            stability_score,
            final_research_question
        )

        logger.debug("Manually lock the data instance if necessary (complex locking is usually done via raw query or dedicated manager)")
        exploration_data = ExplorationPhaseData.objects.select_for_update().get(workflow=workflow)

        return workflow, exploration_data

def get_conceptual_nodes_recommendation(workflow_id: str, canvas_id: str):
    """
    """
    CanvasNodeRelation = apps.get_model('canvases', 'CanvasNodeRelation')
    canvas_node_relations = CanvasNodeRelation.objects.filter(canvas__id=canvas_id).all()
    recommended_nodes = [relation for relation in canvas_node_relations if relation.status == EntityStatus.AI_EXTRACTED]
    if recommended_nodes:
        return recommended_nodes

    ConceptualNode = apps.get_model('canvases', 'ConceptualNode')
    on_pool_nodes = ConceptualNode.objects.filter(workflow__workflow_id=workflow_id).exclude(canvases__id=canvas_id).distinct()

    on_canvas_str = "\n".join([f"- [{relation.node.node_type}] {relation.node.label} (ID: {relation.node.id})" for relation in canvas_node_relations])
    pool_str = "\n".join([f"- [{node.node_type}] {node.label} (ID: {node.id})" for node in on_pool_nodes])

    ConceptualEdge = apps.get_model('canvases', 'ConceptualEdge')
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
        'next_event_type': '',
        'next_event_queue': ''
    }

    publish_event.delay(
        event_type=AgentRequest.name,
        payload=payload,
        queue=AgentRequest.queue
    )


def get_or_create_exploration_data(workflow: ResearchWorkflow, stability_score: int, final_research_question: str) -> ExplorationPhaseData:
    """
    Retrieves or creates the explorationPhaseData linked to the workflow state.
    Handles phase-specific default value initialization.

    NOTE: Don't be decorate this function with @sync_to_async.
    This function is used by atomic_read_and_lock_exploration_data and is
    intended to be called within an atomic transaction.
    """

    logger.info("Using get_or_create to safely handle the OneToOne relationship")
    exploration_data, created = ExplorationPhaseData.objects.get_or_create(
        workflow=workflow,
    )

    exploration_data.stability_score = stability_score
    exploration_data.final_research_question = final_research_question
    exploration_data.save()

    publish_event.delay(
        event_type=CreateNewCanvas.name,
        payload={'workflow_id': workflow.workflow_id},
        queue=CreateNewCanvas.queue
    )

    return exploration_data

def get_sidebar_registry_info(workflow_id: UUID, serializer_class=None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    ConceptualNode = apps.get_model('canvases', 'ConceptualNode')

    exploration_instance = ExplorationPhaseData.objects.select_related(
        'workflow',
    ).get(
        workflow_id=workflow_id
    )

    nodes = ConceptualNode.objects.filter(workflow=exploration_instance.workflow).distinct()

    sidebar_registry_info = SimpleNamespace(
        stability_score=exploration_instance.stability_score,
        final_research_question=exploration_instance.final_research_question,
        nodes=nodes,
    )

    serializer = serializer_class(sidebar_registry_info)
    return serializer.data
