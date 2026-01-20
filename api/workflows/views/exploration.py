import logging

from asgiref.sync import sync_to_async
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from rest_framework import status
from rest_framework.response import Response
from workflows.models import ExplorationPhaseData
from workflows.serializers import SidebarRegistryInfoSerializer
from workflows.utils import get_sidebar_registry_info

from .base import WorkflowBaseView

logger = logging.getLogger(__name__)


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
