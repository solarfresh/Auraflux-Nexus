import logging

from adrf.views import APIView
from django.contrib.auth import get_user_model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from messaging.constants import InitiationEAStreamRequest
from messaging.tasks import publish_event
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import KuhlthauStage, ResearchWorkflowState
from .serializers import (WorkflowChatInputRequestSerializer,
                          WorkflowChatInputResponseSerializer)
from .utils import atomic_read_and_lock_initiation_data

User = get_user_model()
logger = logging.getLogger(__name__)


class WorkflowChatInputView(APIView):
    """
    Handles POST requests for chat input within a specific workflow session.
    Routes the input to the corresponding agent handler based on current_stage.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Submit Chat Input for Workflow Session",
        description=(
            "Accepts user chat input for a specific workflow session identified by session_id. "
            "Validates the workflow state and routes the input to the appropriate agent handler based on the current stage."
        ),
        parameters=[
            OpenApiParameter(
                name="session_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the workflow session.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        request=WorkflowChatInputRequestSerializer,
        responses={
            202: WorkflowChatInputResponseSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            409: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Successful Submission',
                value={"status": "processing", "message": "Chat input request submitted. Please await the real-time response."},
                response_only=True,
                status_codes=['202']
            ),
            OpenApiExample(
                'Missing user_message',
                value={"error": "user_message is required."},
                response_only=True,
                status_codes=['400']
            ),
        ]
    )
    async def post(self, request, session_id):
        user_message = request.data.get('user_message')
        ea_agent_role_name = request.data.get('ea_agent_role_name', 'ExplorerAgent')
        if not user_message:
            return Response({"error": "user_message is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # State Locking and Initial Check (Ensure Atomicity)
        try:
            # Atomic read and lock (runs in a sync thread via @sync_to_async)
            workflow_state, phase_data = await atomic_read_and_lock_initiation_data(
                session_id=session_id,
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
            "session_id": str(session_id),
            "user_id": user.id,
            "user_message": user_message,
            "ea_agent_role_name": ea_agent_role_name,
            "current_clarity_score": phase_data.clarity_score,
            "last_da_execution_time": phase_data.last_da_execution_time.isoformat() if phase_data.last_da_execution_time else None,
            "keyword_stability_count": phase_data.keyword_stability_count,
            "da_activation_threshold": phase_data.da_activation_threshold,
            "current_chat_history": phase_data.chat_history
        }

        publish_event.delay(
            event_type=InitiationEAStreamRequest.name,
            payload=event_payload,
            queue=InitiationEAStreamRequest.queue
        )

        logger.info("Published %s event for session ID: %s", InitiationEAStreamRequest.name, session_id)

        return Response(
            {"status": "processing", "message": "Chat input request submitted. Please await the real-time response."},
            status=status.HTTP_202_ACCEPTED
        )
