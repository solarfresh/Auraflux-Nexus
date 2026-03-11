import logging

from adrf.views import APIView
from asgiref.sync import sync_to_async
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .utils import (delete_canvas_node_relation_by_constraint,
                    get_conceptual_graph,
                    update_canvas_node_relation_by_constraint)

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


class ConceptualNodeView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Delete Canvas Node Relation by node_id on a Canvas",
        description=(
            "Deletes the relationship between a node and a canvas based on the provided node_id and canvas_id. "
            "This operation removes the node from the canvas, effectively updating the conceptual graph. "
            "It is important to note that this action does not delete the node itself from the database, "
            "but rather dissociates it from the specified canvas."
        ),
        parameters=[
            OpenApiParameter(
                name="canvas_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the canvas for which to recommend conceptual nodes.",
                required=True,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="node_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the node to be removed from the canvas.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ]
    )
    async def delete(self, request, canvas_id, node_id):
        await sync_to_async(delete_canvas_node_relation_by_constraint)(
            canvas_id=canvas_id,
            node_id=node_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Update Canvas Node Relation by node_id on a Canvas",
        description=(
            "Updates the relationship between a node and a canvas based on the provided node_id and canvas_id. "
            "This operation modifies the conceptual graph by updating the node's position or rationale on the canvas."
        ),
        parameters=[
            OpenApiParameter(
                name="canvas_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the canvas for which to recommend conceptual nodes.",
                required=True,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="node_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the node to be removed from the canvas.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ]
    )
    async def put(self, request, canvas_id, node_id):
        label = request.data.pop('label')
        relation = request.data

        relation_data = await sync_to_async(update_canvas_node_relation_by_constraint)(
            canvas_id=canvas_id,
            node_id=node_id,
            data=relation
        )

        return Response(relation_data, status=status.HTTP_200_OK)
