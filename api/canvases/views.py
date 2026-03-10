import logging

from asgiref.sync import sync_to_async
from adrf.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .utils import get_conceptual_graph

logger = logging.getLogger(__name__)


class ConceptualCanvasView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Conceptual Graph for Canvas",
        description=(
            "Retrieves the conceptual graph for a given canvas, including nodes and edges. "
            "The response includes the nodes with their positions and rationales, as well as the edges"
            " connecting the nodes with their respective weights. This endpoint is essential for "
            "visualizing the conceptual structure of the canvas and understanding the relationships "
            "between different concepts."
        ),
        parameters=[
            OpenApiParameter(
                name="canvas_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the canvas for which to recommend conceptual nodes.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ]
    )
    async def get(self, request, canvas_id):
        conceptual_graph = await sync_to_async(get_conceptual_graph)(canvas_id=canvas_id)
        return Response(conceptual_graph, status=status.HTTP_200_OK)
