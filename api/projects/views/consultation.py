import logging

from asgiref.sync import sync_to_async
from core.constants import ISPStage
from core.utils import get_serialized_data
from django.db.models import Model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from messaging.constants import ConsultationEAStreamRequest
from messaging.tasks import publish_event
from rest_framework import status
from rest_framework.response import Response
from projects.models import (ChatHistoryEntry, ConsultationPhaseData,
                              ResearchProject)
from projects.serializers import (ChatEntryHistorySerializer,
                                   ProjectChatInputRequestSerializer,
                                   ProjectChatInputResponseSerializer)
from projects.utils import atomic_read_and_lock_consultation_data

from .base import ProjectBaseView

logger = logging.getLogger(__name__)


class ProjectChatInputView(ProjectBaseView):
    """
    Handles POST requests for chat input within a specific project session.
    Routes the input to the corresponding agent handler based on current_stage.
    """

    @extend_schema(
        summary="Submit Chat Input for Project Session",
        description=(
            "Accepts user chat input for a specific project session identified by project_id. "
            "Validates the project state and routes the input to the appropriate agent handler based on the current stage."
        ),
        parameters=[
            OpenApiParameter(
                name="project_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the project session.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        request=ProjectChatInputRequestSerializer,
        responses={
            202: ProjectChatInputResponseSerializer,
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
    async def post(self, request, project_id):
        user_message = request.data.get('user_message')
        ea_agent_role_name = request.data.get('ea_agent_role_name', 'ExplorerAgent')
        if not user_message:
            return Response({"error": "user_message is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # State Locking and Initial Check (Ensure Atomicity)
        try:
            # Atomic read and lock (runs in a sync thread via @sync_to_async)
            project, phase_data = await sync_to_async(atomic_read_and_lock_consultation_data)(
                project_id=project_id,
                user_id=user.id
            )
        except ResearchProject.DoesNotExist:
            return Response({"error": "Project session not found or access denied."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"DB lock or retrieval error: {e}")
            return Response({"error": "Database access error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if project.current_stage != ISPStage.CONSULTATION:
            error_msg = (
                f"Operation not allowed. Current stage is '{project.current_stage}', "
                f"expected '{ISPStage.CONSULTATION}' for this chat endpoint."
            )
            return Response({"error": error_msg}, status=status.HTTP_409_CONFLICT)

        event_payload = {
            "project_id": str(project_id),
            "user_id": user.id,
            "user_message": user_message,
            "ea_agent_role_name": ea_agent_role_name,
            "discarded_elements_list": [],
            "conversation_summary_of_old_history": phase_data.conversation_summary,
            'last_analysis_sequence_number': phase_data.last_analysis_sequence_number,
            "current_chat_history": await sync_to_async(get_serialized_data)({'project_id': project_id}, ChatHistoryEntry, ChatEntryHistorySerializer, many=True)
        }

        publish_event.delay(
            event_type=ConsultationEAStreamRequest.name,
            payload=event_payload,
            queue=ConsultationEAStreamRequest.queue
        )

        logger.info("Published %s event for session ID: %s", ConsultationEAStreamRequest.name, project_id)

        return Response(
            {"status": "processing", "message": "Chat input request submitted. Please await the real-time response."},
            status=status.HTTP_202_ACCEPTED
        )
