import logging

from adrf.views import APIView
from asgiref.sync import sync_to_async
from core.utils import (get_serialized_data, get_serialized_data_by_id,
                        update_serialized_data_by_id)
from django.apps import apps
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from projects.models import ChatHistoryEntry, ResearchProject
from projects.serializers import ChatEntryHistorySerializer, ProjectSerialize
from canvases.serializers import ConceptualNodeSerializer
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


class ProjectDetailView(ProjectBaseView):
    async def get(self, request, project_id):
        data = await sync_to_async(get_serialized_data_by_id)(project_id, ResearchProject, ProjectSerialize)
        return Response(data, status=status.HTTP_200_OK)

    async def put(self, request, project_id):
        request_data = request.data
        try:
            data = await sync_to_async(update_serialized_data_by_id)(project_id, request_data, ResearchProject, ProjectSerialize)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class ConceptualNodeView(ProjectBaseView):
    async def get(self, request, project_id):
        """
        Retrieves ConsultationPhaseData and related topic components for the sidebar.
        """

        user = request.user
        ConceptualNode = apps.get_model('canvases', 'ConceptualNode')

        data = await sync_to_async(get_serialized_data)({'project__id': project_id}, ConceptualNode, ConceptualNodeSerializer, many=True)
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
