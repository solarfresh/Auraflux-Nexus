import logging

from adrf.views import APIView
from asgiref.sync import sync_to_async
from core.utils import get_serialized_data
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from workflows.models import (ChatHistoryEntry, ReflectionLog,
                              ResearchWorkflowState)
from workflows.serializers import (ChatEntryHistorySerializer,
                                   ReflectionLogSerializer)
from workflows.utils import (create_reflection_log_by_session,
                             get_reflection_log_by_session,
                             update_reflection_log_by_id)

logger = logging.getLogger(__name__)


class WorkflowBaseView(APIView):
    """
    Optional base class for all workflow views to share common
    utilities like permission checks or session validation.
    """
    permission_classes = [IsAuthenticated]


class ChatHistoryEntryView(WorkflowBaseView):

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


class SessionReflectionLogView(WorkflowBaseView):

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
            data = await sync_to_async(get_reflection_log_by_session)(session_id, serializer_class=ReflectionLogSerializer)
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


class ReflectionLogView(WorkflowBaseView):

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
