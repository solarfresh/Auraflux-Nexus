import logging

from asgiref.sync import sync_to_async
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from rest_framework import status
from rest_framework.response import Response
from workflows.models import ExplorationPhaseData, ResearchWorkflow
from workflows.serializers import (ExplorationPhaseDataSerializer,
                                   SidebarRegistryInfoSerializer)
from workflows.utils import (atomic_read_and_lock_exploration_data,
                             get_sidebar_registry_info)

from .base import WorkflowBaseView

logger = logging.getLogger(__name__)


class ExplorationPhaseDataView(WorkflowBaseView):
    """

    """

    @extend_schema(
        summary="",
        description="",
        parameters=[
            OpenApiParameter(
                name="session_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the workflow session.",
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
    async def post(self, request, session_id):
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
            workflow, phase_data = await sync_to_async(atomic_read_and_lock_exploration_data)(
                session_id=session_id,
                user_id=user.id,
                stability_score=stability_score,
                final_research_question=final_question
            )
        except ResearchWorkflow.DoesNotExist:
            return Response({"error": "Workflow session not found or access denied."}, status=status.HTTP_404_NOT_FOUND)
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


class SidebarRegistryInfoView(WorkflowBaseView):

    @extend_schema(
        summary="Retrieve Exploration Phase Sidebar Data",
        description=(
            "Fetches all structured data (Stability Score, Keywords, Scope, Reflection) "
            "required to render the Sidebar UI during the Exploration phase."
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
            200: SidebarRegistryInfoSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def get(self, request, session_id):
        """
        Retrieves InitiationPhaseData and related topic components for the sidebar.
        """

        try:
            sidebar_registry_info = await sync_to_async(get_sidebar_registry_info)(session_id, SidebarRegistryInfoSerializer)
        except ExplorationPhaseData.DoesNotExist:
            return Response(
                {"detail": f"Initiation data not found for session {session_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(sidebar_registry_info, status=status.HTTP_200_OK)
