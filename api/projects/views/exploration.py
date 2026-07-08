import logging

from asgiref.sync import sync_to_async
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from core.utils import get_serialized_data
from rest_framework import status
from rest_framework.response import Response
from projects.models import ResearchProject, ExplorationPhaseData
from projects.serializers import ExplorationPhaseDataSerializer
from projects.utils import atomic_read_and_lock_exploration_data

from .base import ProjectBaseView

logger = logging.getLogger(__name__)


class ExplorationPhaseDataView(ProjectBaseView):
    """
    This view handles the creation and retrieval of ExplorationPhaseData for
    a given project session. It ensures that the data is accessed and modified
    in an atomic manner to prevent race conditions and maintain data integrity
    during the Exploration phase of the project.
    """

    async def get(self, request, project_id):
        data = await sync_to_async(get_serialized_data)({'project__id': project_id}, ExplorationPhaseData, ExplorationPhaseDataSerializer, many=False)
        logger.info(data)
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create or Retrieve Exploration Phase Data",
        description=(
            "Creates or retrieves the ExplorationPhaseData for a given project "
            "session. This endpoint ensures atomic access to the data to prevent "
            "race conditions during the Exploration phase."),
        parameters=[
            OpenApiParameter(
                name="project_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the project session.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        request=ExplorationPhaseDataSerializer,
        responses={
            201: ExplorationPhaseDataSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            409: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Missing stabilityScore',
                value={"error": "stabilityScore is required."},
                response_only=True,
                status_codes=['400']
            ),
        ]
    )
    async def post(self, request, project_id):
        user = request.user

        # State Locking and Initial Check (Ensure Atomicity)
        try:
            # Atomic read and lock (runs in a sync thread via @sync_to_async)
            project, phase_data = await sync_to_async(atomic_read_and_lock_exploration_data)(
                project_id=project_id,
                user_id=user.id,
            )
        except ResearchProject.DoesNotExist:
            return Response({"error": "Project session not found or access denied."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"DB lock or retrieval error: {e}")
            return Response({"error": "Database access error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = await sync_to_async(ExplorationPhaseDataSerializer)(phase_data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
