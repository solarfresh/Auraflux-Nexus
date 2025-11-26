import json
import logging

from core.celery_app import celery_app
from messaging.constants import DICHOTOMY_SUGGESTION_COMPLETED
from realtime.utils import send_ws_notification
from workflows.models import WorkflowState

logger = logging.getLogger(__name__)

@celery_app.task(name='handle_suggestion_completion_event', ignore_result=True)
def handle_suggestion_completion_event(event_type: str, payload: dict):
    """
    Consumer task for the DICHOTOMY_SUGGESTION_COMPLETED event.

    1. Updates the WorkflowState cache (Persistence).
    2. Sends a WebSocket notification to the user (Real-time update).

    This function couples to the WorkflowState model and the realtime utility.
    """
    task_id = handle_suggestion_completion_event.request.id

    # Ensure this is the event we are expecting (for safety)
    if event_type != DICHOTOMY_SUGGESTION_COMPLETED:
        logger.warning("Received unexpected event type: %s", event_type)
        return

    workflow_state_id = payload.get('workflow_state_id')
    suggestions_data = payload.get('suggestions')
    user_id = payload.get('user_id')

    if not workflow_state_id:
        logger.error("Missing workflow_state_id in event payload for task ID: %s", task_id)
        return

    if not user_id:
        logger.error("Missing user_id in event payload for task ID: %s", task_id)
        return

    if suggestions_data is None:
        logger.error("Missing suggestions data in event payload for task ID: %s", task_id)
        return

    logger.info("Persistence starting for WF ID %s. Updating cache.", workflow_state_id)

    try:
        # 1. Update WorkflowState (Persistence)
        # We use filter().update() for atomic writing.
        rows_updated = WorkflowState.objects.filter(pk=workflow_state_id).update(
            suggested_dichotomies_cache=suggestions_data
        )

        if rows_updated == 0:
            logger.error("WorkflowState ID %s not found during persistence update.", workflow_state_id)
            return

        logger.info("Workflow state %s successfully updated with %d suggestions.", workflow_state_id, len(suggestions_data))

        # 2. Trigger WebSocket Notification (Decoupling with realtime app)
        send_ws_notification(
            user_id=user_id,
            event_type="dichotomy_suggestions_complete",
            payload={
                "message": "Strategic dichotomies are ready for review.",
                "workflow_state_id": workflow_state_id,
                'suggestions': suggestions_data
            }
        )
        logger.info("WebSocket notification sent to user %s.", user_id)

    except Exception as e:
        logger.critical("Persistence failed for WorkflowState ID %s: %s", workflow_state_id, str(e))
        # Re-raise to signal Celery failure
        raise