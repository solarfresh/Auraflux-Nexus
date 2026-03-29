import logging

from asgiref.sync import sync_to_async
from core.constants import ISPStep
from core.utils import get_serialized_data
from django.db.models import Model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from messaging.constants import InitiationEAStreamRequest
from messaging.tasks import publish_event
from rest_framework import status
from rest_framework.response import Response
from projects.models import (ChatHistoryEntry, InitiationPhaseData,
                              ResearchProject)
from projects.serializers import (ChatEntryHistorySerializer,
                                   RefinedTopicSerializer,
                                   ProjectChatInputRequestSerializer,
                                   ProjectChatInputResponseSerializer)
from projects.utils import (atomic_read_and_lock_initiation_data,
                             create_topic_keyword_by_session,
                             create_topic_scope_element_by_session,
                             get_refined_topic_instance,
                             get_topic_keyword_by_session,
                             get_topic_scope_element_by_session)

from .base import ProjectBaseView

logger = logging.getLogger(__name__)


class RefinedTopicView(ProjectBaseView):

    @extend_schema(
        summary="Retrieve Initiation Phase Sidebar Data",
        description=(
            "Fetches all structured data (Stability Score, Feasibility, Keywords, Scope, Reflection) "
            "required to render the Sidebar UI during the INITIATION phase."
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
        responses={
            200: RefinedTopicSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, project_id):
        """
        Retrieves InitiationPhaseData and related topic components for the sidebar.
        """

        try:
            refined_topic = await sync_to_async(get_refined_topic_instance)(project_id, RefinedTopicSerializer)
        except InitiationPhaseData.DoesNotExist:
            return Response(
                {"detail": f"Initiation data not found for session {project_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(refined_topic, status=status.HTTP_200_OK)


class SessionTopicKeywordView(ProjectBaseView):

    @extend_schema(
        summary="Retrieve Topic Keywords for Project Session",
        description=(
            "Fetches the list of Topic Keywords associated with a specific project session identified by project_id."
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
        responses={
            200: ProcessedKeywordSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, project_id):
        try:
            data = await sync_to_async(get_topic_keyword_by_session)(project_id, serializer_class=ProcessedKeywordSerializer)
        except Model.DoesNotExist:
            return Response({"detail": f"Topic keywords not found for session {project_id}."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add a New Topic Keyword",
        description=(
            "Adds a new Topic Keyword associated with the specified project session."
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
        request=ProcessedKeywordSerializer,
        responses={
            201: ProcessedKeywordSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def post(self, request, project_id):
        keyword_text = request.data.get('text')
        keyword_status = request.data.get('status', None)
        if not keyword_text:
            return Response(
                {"detail": "text is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = await sync_to_async(create_topic_keyword_by_session)(project_id, keyword_text, keyword_status, serializer_class=ProcessedKeywordSerializer)
        except ResearchProject.DoesNotExist:
            return Response(
                {"detail": f"Research project state not found for session {project_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Model.DoesNotExist:
            return Response(
                {"detail": f"Failed to create keyword for session {project_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_201_CREATED)


class SessionTopicScopeElementView(ProjectBaseView):

    @extend_schema(
        summary="Retrieve Topic Scope Elements for Project Session",
        description=(
            "Fetches the list of Topic Scope Elements associated with a specific project session identified by project_id."
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
        responses={
            200: ProcessedScopeSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, project_id):
        try:
            data = await sync_to_async(get_topic_scope_element_by_session)(project_id, serializer_class=ProcessedScopeSerializer)
        except Model.DoesNotExist:
            return Response({"detail": f"Topic scope elements not found for session {project_id}."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add a New Topic Scope Element",
        description=(
            "Adds a new Topic Scope Element associated with the specified project session."
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
        request=ProcessedScopeSerializer,
        responses={
            201: ProcessedScopeSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def post(self, request, project_id):
        scope_label = request.data.get('label')
        scope_value = request.data.get('value')
        scope_status = request.data.get('status', None)
        if not scope_label:
            return Response(
                {"detail": "label is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not scope_value:
            return Response(
                {"detail": "value is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = await sync_to_async(create_topic_scope_element_by_session)(project_id, scope_value, scope_label, scope_status, serializer_class=ProcessedScopeSerializer)
        except ResearchProject.DoesNotExist:
            return Response(
                {"detail": f"Research project state not found for session {project_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Model.DoesNotExist:
            return Response(
                {"detail": f"Failed to create scope for session {project_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_201_CREATED)


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
            project, phase_data = await sync_to_async(atomic_read_and_lock_initiation_data)(
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

        if project.current_stage != ISPStep.DEFINITION:
            error_msg = (
                f"Operation not allowed. Current stage is '{project.current_stage}', "
                f"expected '{ISPStep.DEFINITION}' for this chat endpoint."
            )
            return Response({"error": error_msg}, status=status.HTTP_409_CONFLICT)

        TopicKeyword = project.keywords.model
        TopicScopeElement = project.scope_elements.model

        event_payload = {
            "project_id": str(project_id),
            "user_id": user.id,
            "user_message": user_message,
            "ea_agent_role_name": ea_agent_role_name,
            "final_question_draft": phase_data.final_research_question,
            "locked_keywords_list": await sync_to_async(get_serialized_data)({'object_id': project_id, 'status': 'LOCKED'}, TopicKeyword, ProcessedKeywordSerializer, many=True),
            "locked_scope_elements_list": await sync_to_async(get_serialized_data)({'object_id': project_id, 'status': 'LOCKED'}, TopicScopeElement, ProcessedScopeSerializer, many=True),
            "discarded_elements_list": [],
            "conversation_summary_of_old_history": phase_data.conversation_summary,
            'last_analysis_sequence_number': phase_data.last_analysis_sequence_number,
            "current_chat_history": await sync_to_async(get_serialized_data)({'project_id': project_id}, ChatHistoryEntry, ChatEntryHistorySerializer, many=True)
        }

        publish_event.delay(
            event_type=InitiationEAStreamRequest.name,
            payload=event_payload,
            queue=InitiationEAStreamRequest.queue
        )

        logger.info("Published %s event for session ID: %s", InitiationEAStreamRequest.name, project_id)

        return Response(
            {"status": "processing", "message": "Chat input request submitted. Please await the real-time response."},
            status=status.HTTP_202_ACCEPTED
        )
