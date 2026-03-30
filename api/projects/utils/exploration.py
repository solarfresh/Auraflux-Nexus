import logging
from types import SimpleNamespace
from uuid import UUID

from core.constants import EntityStatus
from django.apps import apps
from django.db import transaction
from django.shortcuts import get_object_or_404
from messaging.constants import CreateNewCanvas, RecommendConceptualNodes
from messaging.tasks import publish_event
from projects.models import ExplorationPhaseData, ResearchProject

logger = logging.getLogger(__name__)

def atomic_read_and_lock_exploration_data(
    project_id: UUID,
    user_id: UUID,
    stability_score: int,
    final_research_question: str
) -> tuple[ResearchProject, ExplorationPhaseData]:
    """
    Executes a single atomic transaction to lock the state and load the exploration data.
    This is the function called by the ProjectChatInputView.
    """

    # Ensures the entire sequence is locked and atomic
    with transaction.atomic():
        # Retrieve and LOCK the main state
        # Note: Must use select_for_update() for locking
        project = get_object_or_404(
            ResearchProject.objects.select_for_update(),
            project_id=project_id,
            user_id=user_id
        )

        # Retrieve or Create and LOCK the phase data
        # We need to get or create the ExplorationPhaseData instance.
        # Since it is a OneToOne relationship, the lock on the parent often suffices,
        # but select_for_update() is safer if the instance exists.

        logger.debug("call the synchronous helper function *within* the atomic block")
        exploration_data = get_or_create_exploration_data(
            project,
            stability_score,
            final_research_question
        )

        logger.debug("Manually lock the data instance if necessary (complex locking is usually done via raw query or dedicated manager)")
        exploration_data = ExplorationPhaseData.objects.select_for_update().get(project=project)

        return project, exploration_data

def get_conceptual_nodes_recommendation(user_id: UUID, project_id: UUID, canvas_id: UUID):
    """
    """
    publish_event.delay(
        event_type=RecommendConceptualNodes.name,
        payload={
            'user_id': user_id,
            'canvas_id': canvas_id,
            'project_id': project_id
        },
        queue=RecommendConceptualNodes.queue
    )

def get_or_create_exploration_data(project: ResearchProject, stability_score: int, final_research_question: str) -> ExplorationPhaseData:
    """
    Retrieves or creates the explorationPhaseData linked to the project state.
    Handles phase-specific default value initialization.

    NOTE: Don't be decorate this function with @sync_to_async.
    This function is used by atomic_read_and_lock_exploration_data and is
    intended to be called within an atomic transaction.
    """

    logger.info("Using get_or_create to safely handle the OneToOne relationship")
    exploration_data, created = ExplorationPhaseData.objects.get_or_create(
        project=project,
    )

    exploration_data.stability_score = stability_score
    exploration_data.final_research_question = final_research_question
    exploration_data.save()

    publish_event.delay(
        event_type=CreateNewCanvas.name,
        payload={'project_id': project.id},
        queue=CreateNewCanvas.queue
    )

    return exploration_data

def get_sidebar_registry_info(project_id: UUID, serializer_class=None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    ConceptualNode = apps.get_model('canvases', 'ConceptualNode')

    exploration_instance = ExplorationPhaseData.objects.select_related(
        'project',
    ).get(
        project_id=project_id
    )

    nodes = ConceptualNode.objects.filter(project=exploration_instance.project).distinct()

    sidebar_registry_info = SimpleNamespace(
        stability_score=exploration_instance.stability_score,
        final_research_question=exploration_instance.final_research_question,
        activated_canvas_id=exploration_instance.active_canvas_id,
        nodes=nodes,
    )

    serializer = serializer_class(sidebar_registry_info)
    return serializer.data
