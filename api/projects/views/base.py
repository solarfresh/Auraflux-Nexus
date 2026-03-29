import logging

from adrf.views import APIView
from asgiref.sync import sync_to_async
from core.utils import get_serialized_data
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from projects.models import ChatHistoryEntry, ReflectionLog, ResearchProject
from projects.serializers import (ChatEntryHistorySerializer, ProjectSerialize,
                                  ReflectionLogSerializer)
from projects.utils import (create_reflection_log_by_session,
                            get_reflection_log_by_project,
                            update_reflection_log_by_id)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class ProjectBaseView(APIView):
    """
    Optional base class for all project views to share common
    utilities like permission checks or session validation.
    """
    permission_classes = [IsAuthenticated]


class ProjectView(ProjectBaseView):
    async def get(self, request):
        user = request.user

        data = await sync_to_async(get_serialized_data)({'user_id': user.id}, ResearchProject, ProjectSerialize, many=True)
        return Response(data, status=status.HTTP_200_OK)


class ChatHistoryEntryView(ProjectBaseView):

    @extend_schema(
        summary="Retrieve Chat History for Project Session",
        description=(
            "Fetches the complete chat history associated with a specific project session identified by project_id."
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
    async def get(self, request, project_id):
        data = await sync_to_async(get_serialized_data)({'project_id': project_id}, ChatHistoryEntry, ChatEntryHistorySerializer, many=True)
        return Response(data, status=status.HTTP_200_OK)


class SessionReflectionLogView(ProjectBaseView):

    @extend_schema(
        summary="Retrieve Reflection Log for Project Session",
        description=(
            "Fetches the list of Reflection Logs associated with a specific project session identified by project_id."
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
            200: ReflectionLogSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, project_id):
        try:
            data = await sync_to_async(get_reflection_log_by_project)(project_id, serializer_class=ReflectionLogSerializer)
        except ReflectionLog.DoesNotExist:
            return Response({"detail": f"Reflection logs not found for session {project_id}."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add a New Reflection Log",
        description=(
            "Adds a new Reflection Log associated with the specified project session."
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
        request=ReflectionLogSerializer,
        responses={
            201: ReflectionLogSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def post(self, request, project_id):
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
                project_id,
                reflection_log_title,
                reflection_log_content,
                reflection_log_status,
                serializer_class=ReflectionLogSerializer)
        except ResearchProject.DoesNotExist:
            return Response(
                {"detail": f"Research project state not found for session {project_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ReflectionLog.DoesNotExist:
            return Response(
                {"detail": f"Failed to create reflection log for session {project_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_201_CREATED)


class ReflectionLogView(ProjectBaseView):

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
