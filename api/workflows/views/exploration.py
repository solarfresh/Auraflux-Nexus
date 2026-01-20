import logging

from asgiref.sync import sync_to_async

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)

from workflows.utils import get_refined_topic_instance
from .base import WorkflowBaseView

logger = logging.getLogger(__name__)


class RefinedTopicView(WorkflowBaseView):

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
            refined_topic = await sync_to_async(get_refined_topic_instance)(session_id, RefinedTopicSerializer)
        except InitiationPhaseData.DoesNotExist:
            return Response(
                {"detail": f"Initiation data not found for session {session_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(refined_topic, status=status.HTTP_200_OK)
