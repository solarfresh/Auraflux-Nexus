import logging
import uuid

from adrf.views import APIView
from django.contrib.auth import get_user_model
from messaging.constants import INITIATION_CHAT_INPUT_REQUESTED
from messaging.tasks import publish_event
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import KuhlthauStage, ResearchWorkflowState
from .utils import atomic_read_and_lock_initiation_data

User = get_user_model()
logger = logging.getLogger(__name__)


class WorkflowChatInputView(APIView):
    """
    Handles POST requests for chat input within a specific workflow session.
    Routes the input to the corresponding agent handler based on current_stage.
    """

    permission_classes = [IsAuthenticated]

    async def post(self, request, session_id):
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            return Response({"error": "Invalid session_id format."}, status=status.HTTP_400_BAD_REQUEST)

        user_message = request.data.get('user_message')
        if not user_message:
            return Response({"error": "user_message is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # State Locking and Initial Check (Ensure Atomicity)
        try:
            # Atomic read and lock (runs in a sync thread via @sync_to_async)
            workflow_state, phase_data = await atomic_read_and_lock_initiation_data(
                session_id=session_uuid,
                user_id=user.id
            )
        except ResearchWorkflowState.DoesNotExist:
            return Response({"error": "Workflow session not found or access denied."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"DB lock or retrieval error: {e}")
            return Response({"error": "Database access error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if workflow_state.current_stage != KuhlthauStage.INITIATION:
            error_msg = (
                f"Operation not allowed. Current stage is '{workflow_state.current_stage}', "
                f"expected '{KuhlthauStage.INITIATION}' for this chat endpoint."
            )
            return Response({"error": error_msg}, status=status.HTTP_409_CONFLICT)

        event_payload = {
            "session_id": str(session_uuid),
            "user_id": user.id,
            "user_message": user_message,
            "current_clarity_score": phase_data.clarity_score,
            "last_da_execution_time": phase_data.last_da_execution_time.isoformat() if phase_data.last_da_execution_time else None,
            "keyword_stability_count": phase_data.keyword_stability_count,
            "da_activation_threshold": phase_data.da_activation_threshold,
            "current_chat_history": phase_data.chat_history
        }

        publish_event.delay(
            event_type=INITIATION_CHAT_INPUT_REQUESTED,
            payload=event_payload
        )

        logger.info("Published %s event for session ID: %s", INITIATION_CHAT_INPUT_REQUESTED, session_id)

        return Response(
            {"status": "processing", "message": "Chat input request submitted. Please await the real-time response."},
            status=status.HTTP_202_ACCEPTED
        )
