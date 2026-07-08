import logging
from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from messaging.constants import CreateNewCanvas
from messaging.tasks import publish_event
from projects.models import ExplorationPhaseData, ResearchProject

logger = logging.getLogger(__name__)

def atomic_read_and_lock_exploration_data(
    project_id: UUID,
    user_id: UUID,
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
        )

        logger.debug("Manually lock the data instance if necessary (complex locking is usually done via raw query or dedicated manager)")
        exploration_data = ExplorationPhaseData.objects.select_for_update().get(project=project)

        return project, exploration_data

def get_or_create_exploration_data(project: ResearchProject) -> ExplorationPhaseData:
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

    exploration_data.save()

    publish_event.delay(
        event_type=CreateNewCanvas.name,
        payload={'project_id': project.id},
        queue=CreateNewCanvas.queue
    )

    return exploration_data
