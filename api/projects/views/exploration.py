import logging

from asgiref.sync import sync_to_async
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from projects.models import ExplorationPhaseData, ResearchProject
from projects.serializers import (ExplorationPhaseDataSerializer,
                                   SidebarRegistryInfoSerializer)
from projects.utils import (atomic_read_and_lock_exploration_data,
                             get_conceptual_nodes_recommendation,
                             get_sidebar_registry_info)

from .base import ProjectBaseView

logger = logging.getLogger(__name__)


class ConceptualNodesRecommendationView(ProjectBaseView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Trigger Conceptual Nodes Recommendation",
        description=(
            "Initiates the process to recommend conceptual nodes based on the current canvas and project state. "
            "This endpoint is designed to be called after the Exploration phase data is set, and it will publish an event to the message queue to start the recommendation process asynchronously."
        ),
        parameters=[
            OpenApiParameter(
                name="project_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the project session.",
                required=True,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="canvas_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the canvas for which to recommend conceptual nodes.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ]
    )
    async def post(self, request, project_id, canvas_id):
        user = request.user
        await sync_to_async(get_conceptual_nodes_recommendation)(user.id, project_id, canvas_id)
        return Response(
            {"status": "processing", "message": "Conceptual nodes recommendation is being processed."},
            status=status.HTTP_202_ACCEPTED
        )


class ExplorationPhaseDataView(ProjectBaseView):
    """
    This view handles the creation and retrieval of ExplorationPhaseData for
    a given project session. It ensures that the data is accessed and modified
    in an atomic manner to prevent race conditions and maintain data integrity
    during the Exploration phase of the project.
    """
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
        stability_score = request.data.get('stabilityScore')
        final_question = request.data.get('finalQuestion')

        if not stability_score:
            return Response({"error": "stabilityScore is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not final_question:
            return Response({"error": "finalQuestion is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # State Locking and Initial Check (Ensure Atomicity)
        try:
            # Atomic read and lock (runs in a sync thread via @sync_to_async)
            project, phase_data = await sync_to_async(atomic_read_and_lock_exploration_data)(
                project_id=project_id,
                user_id=user.id,
                stability_score=stability_score,
                final_research_question=final_question
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


class SidebarRegistryInfoView(ProjectBaseView):

    @extend_schema(
        summary="Retrieve Exploration Phase Sidebar Data",
        description=(
            "Fetches all structured data (Stability Score, Keywords, Scope, Reflection) "
            "required to render the Sidebar UI during the Exploration phase."
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
            200: SidebarRegistryInfoSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, project_id):
        """
        Retrieves InitiationPhaseData and related topic components for the sidebar.
        """

        try:
            sidebar_registry_info = await sync_to_async(get_sidebar_registry_info)(project_id, SidebarRegistryInfoSerializer)
        except ExplorationPhaseData.DoesNotExist:
            return Response(
                {"detail": f"Initiation data not found for session {project_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(sidebar_registry_info, status=status.HTTP_200_OK)
