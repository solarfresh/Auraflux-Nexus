import logging

from adrf.views import APIView
from asgiref.sync import sync_to_async
from core.utils import get_serialized_data
from django.contrib.auth import get_user_model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from messaging.constants import InitiationEAStreamRequest
from messaging.tasks import publish_event
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (ChatHistoryEntry, InitiationPhaseData, KuhlthauStage,
                     ReflectionLog, ResearchWorkflowState, TopicKeyword,
                     TopicScopeElement)
from .serializers import (ChatEntryHistorySerializer, RefinedTopicSerializer,
                          ReflectionLogSerializer, TopicKeywordSerializer,
                          TopicScopeElementSerializer,
                          WorkflowChatInputRequestSerializer,
                          WorkflowChatInputResponseSerializer)
from .utils import (atomic_read_and_lock_initiation_data,
                    create_reflection_log_by_session,
                    create_topic_keyword_by_session,
                    create_topic_scope_element_by_session,
                    get_refined_topic_instance, get_reflection_log_by_session,
                    get_topic_keyword_by_session,
                    get_topic_scope_element_by_session,
                    update_reflection_log_by_id, update_topic_keyword_by_id,
                    update_topic_scope_element_by_id)

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatHistoryEntryView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Chat History for Workflow Session",
        description=(
            "Fetches the complete chat history associated with a specific workflow session identified by session_id."
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
        request=ChatEntryHistorySerializer,
        responses={
            200: ChatEntryHistorySerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Successful Persistence',
                value={
                    "id": 1,
                    "role": "user",
                    "content": "Hello, how can I assist you?",
                    "name": "Explorer Agent",
                    "sequence_number": 1,
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Invalid Data',
                value={"error": "Invalid input data."},
                response_only=True,
                status_codes=['400']
            ),
        ]
    )
    async def get(self, request, session_id):
        data = await get_serialized_data({'workflow_state_id': session_id}, ChatHistoryEntry, ChatEntryHistorySerializer, many=True)
        return Response(data, status=status.HTTP_200_OK)


class RefinedTopicView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Initiation Phase Sidebar Data",
        description=(
            "Fetches all structured data (Stability Score, Feasibility, Keywords, Scope, Reflection) "
            "required to render the Sidebar UI during the INITIATION phase."
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
        responses={
            200: RefinedTopicSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, session_id):
        """
        Retrieves InitiationPhaseData and related topic components for the sidebar.
        """

        try:
            initiation_instance = await sync_to_async(get_refined_topic_instance)(session_id)
        except InitiationPhaseData.DoesNotExist:
            return Response(
                {"detail": f"Initiation data not found for session {session_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RefinedTopicSerializer(initiation_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SessionReflectionLogView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Reflection Log for Workflow Session",
        description=(
            "Fetches the list of Reflection Logs associated with a specific workflow session identified by session_id."
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
        responses={
            200: ReflectionLogSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, session_id):
        try:
            data = get_reflection_log_by_session(session_id, serializer_class=ReflectionLogSerializer)
        except ReflectionLog.DoesNotExist:
            return Response({"detail": f"Reflection logs not found for session {session_id}."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add a New Reflection Log",
        description=(
            "Adds a new Reflection Log associated with the specified workflow session."
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
        request=ReflectionLogSerializer,
        responses={
            201: ReflectionLogSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def post(self, request, session_id):
        reflection_log_title = request.data.get('title')
        reflection_log_content = request.data.get('content')
        reflection_log_status = request.data.get('status', None)
        if not reflection_log_title:
            return Response(
                {"detail": "title is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not reflection_log_content:
            return Response(
                {"detail": "content is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = await sync_to_async(create_reflection_log_by_session)(
                session_id,
                reflection_log_title,
                reflection_log_content,
                reflection_log_status,
                serializer_class=ReflectionLogSerializer)
        except ResearchWorkflowState.DoesNotExist:
            return Response(
                {"detail": f"Research workflow state not found for session {session_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ReflectionLog.DoesNotExist:
            return Response(
                {"detail": f"Failed to create reflection log for session {session_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_201_CREATED)


class SessionTopicKeywordView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Topic Keywords for Workflow Session",
        description=(
            "Fetches the list of Topic Keywords associated with a specific workflow session identified by session_id."
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
        responses={
            200: TopicKeywordSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, session_id):
        try:
            data = get_topic_keyword_by_session(session_id, serializer_class=TopicKeywordSerializer)
        except TopicKeyword.DoesNotExist:
            return Response({"detail": f"Topic keywords not found for session {session_id}."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add a New Topic Keyword",
        description=(
            "Adds a new Topic Keyword associated with the specified workflow session."
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
        request=TopicKeywordSerializer,
        responses={
            201: TopicKeywordSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def post(self, request, session_id):
        keyword_text = request.data.get('text')
        keyword_status = request.data.get('status', None)
        if not keyword_text:
            return Response(
                {"detail": "text is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = await sync_to_async(create_topic_keyword_by_session)(session_id, keyword_text, keyword_status, serializer_class=TopicKeywordSerializer)
        except ResearchWorkflowState.DoesNotExist:
            return Response(
                {"detail": f"Research workflow state not found for session {session_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except TopicKeyword.DoesNotExist:
            return Response(
                {"detail": f"Failed to create keyword for session {session_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_201_CREATED)


class SessionTopicScopeElementView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Topic Scope Elements for Workflow Session",
        description=(
            "Fetches the list of Topic Scope Elements associated with a specific workflow session identified by session_id."
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
        responses={
            200: TopicScopeElementSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, session_id):
        try:
            data = get_topic_scope_element_by_session(session_id, serializer_class=TopicScopeElementSerializer)
        except TopicScopeElement.DoesNotExist:
            return Response({"detail": f"Topic scope elements not found for session {session_id}."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add a New Topic Scope Element",
        description=(
            "Adds a new Topic Scope Element associated with the specified workflow session."
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
        request=TopicScopeElementSerializer,
        responses={
            201: TopicScopeElementSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def post(self, request, session_id):
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
            data = await sync_to_async(create_topic_scope_element_by_session)(session_id, scope_value, scope_label, scope_status, serializer_class=TopicScopeElementSerializer)
        except ResearchWorkflowState.DoesNotExist:
            return Response(
                {"detail": f"Research workflow state not found for session {session_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except TopicScopeElement.DoesNotExist:
            return Response(
                {"detail": f"Failed to create scope for session {session_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_201_CREATED)


class ReflectionLogView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update an Existing Reflection Log",
        description=(
            "Updates the text and status of an existing Reflection Log identified by log_id."
        ),
        parameters=[
            OpenApiParameter(
                name="log_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the topic keyword.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        request=ReflectionLogSerializer,
        responses={
            200: ReflectionLogSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def put(self, request, log_id):
        reflection_log_title = request.data.get('title')
        reflection_log_content = request.data.get('content')
        reflection_log_status = request.data.get('status', None)
        if not reflection_log_title:
            return Response(
                {"detail": "title is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not reflection_log_content:
            return Response(
                {"detail": "content is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = await sync_to_async(update_reflection_log_by_id)(
                log_id,
                reflection_log_title,
                reflection_log_content,
                reflection_log_status,
                serializer_class=ReflectionLogSerializer)
        except ReflectionLog.DoesNotExist:
            return Response(
                {"detail": f"Reflection Log '{log_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)


class TopicKeywordView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update an Existing Topic Keyword",
        description=(
            "Updates the text and status of an existing Topic Keyword identified by keyword_id."
        ),
        parameters=[
            OpenApiParameter(
                name="keyword_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the topic keyword.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        request=TopicKeywordSerializer,
        responses={
            200: TopicKeywordSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def put(self, request, keyword_id):
        keyword_text = request.data.get('text')
        keyword_status = request.data.get('status', None)
        if not keyword_text:
            return Response(
                {"detail": "text is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = await sync_to_async(update_topic_keyword_by_id)(keyword_id, keyword_text, keyword_status, serializer_class=TopicKeywordSerializer)
        except TopicKeyword.DoesNotExist:
            return Response(
                {"detail": f"Keyword '{keyword_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)


class TopicScopeElementView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update an Existing Topic Scope Element",
        description=(
            "Updates the text and status of an existing Topic Scope Element identified by scope_id."
        ),
        parameters=[
            OpenApiParameter(
                name="scope_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the topic scope element.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        request=TopicScopeElementSerializer,
        responses={
            200: TopicScopeElementSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def put(self, request, scope_id):
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
            data = await sync_to_async(update_topic_scope_element_by_id)(scope_id, scope_value, scope_label, scope_status, serializer_class=TopicScopeElementSerializer)
        except TopicScopeElement.DoesNotExist:
            return Response(
                {"detail": f"Scope Element '{scope_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)


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
            workflow_state, phase_data = await sync_to_async(atomic_read_and_lock_initiation_data)(
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

        if workflow_state.current_stage != KuhlthauStage.TOPIC_DEFINITION_LOCKIN:
            error_msg = (
                f"Operation not allowed. Current stage is '{workflow_state.current_stage}', "
                f"expected '{KuhlthauStage.TOPIC_DEFINITION_LOCKIN}' for this chat endpoint."
            )
            return Response({"error": error_msg}, status=status.HTTP_409_CONFLICT)

        event_payload = {
            "session_id": str(session_id),
            "user_id": user.id,
            "user_message": user_message,
            "ea_agent_role_name": ea_agent_role_name,
            "final_question_draft": phase_data.final_research_question,
            "locked_keywords_list": await get_serialized_data({'initiation_data_id': session_id, 'status': 'LOCKED'}, TopicKeyword, TopicKeywordSerializer, many=True),
            "locked_scope_elements_list": await get_serialized_data({'initiation_data_id': session_id, 'status': 'LOCKED'}, TopicScopeElement, TopicScopeElementSerializer, many=True),
            "discarded_elements_list": [],
            "conversation_summary_of_old_history": phase_data.conversation_summary,
            "latest_reflection_entry": phase_data.latest_reflection_entry.entry_text if phase_data.latest_reflection_entry is not None else '',
            'last_analysis_sequence_number': phase_data.last_analysis_sequence_number,
            "current_chat_history": await get_serialized_data({'workflow_state_id': session_id}, ChatHistoryEntry, ChatEntryHistorySerializer, many=True)
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
