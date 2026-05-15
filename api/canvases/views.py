import logging

from adrf.views import APIView
from asgiref.sync import sync_to_async
from core.utils import (delete_instance_by_query,
                        update_serialized_data_by_query)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   OpenApiResponse, extend_schema)
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ConceptualEdge
from .serializers import ConceptualEdgeSerializer
from .utils import (create_conceptual_edge,
                    delete_canvas_node_relation_by_constraint,
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


class ConceptualEdgeView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update an existing conceptual edge",
        description=(
            "Updates the properties of an edge within a specific canvas context. "
            "Allows modifying label, weight, evidence, and AI rationale."
        ),
        request=ConceptualEdgeSerializer,
        responses={
            200: ConceptualEdgeSerializer,
            400: None,
            404: None,
        },
        examples=[
            OpenApiExample(
                'Update Evidence & Weight',
                summary='Updating grounding evidence',
                description='An example of refining the link strength and providing updated agentic audit evidence.',
                value={
                    "label": "Strongly Validates",
                    "type": "VALIDATES",
                    "evidence": "Cross-referenced with newly uploaded dataset B, section 5.",
                    "weight": 0.95,
                    "rationale": "Confidence increased due to multi-source verification.",
                    "metadata": {
                        "last_updated_by": "agent-alpha",
                        "audit_passed": True
                    }
                },
                request_only=True,
            ),
        ],
    )
    async def put(self, request, canvas_id, edge_id):
        data = request.data
        try:
            result = await sync_to_async(update_serialized_data_by_query)(
                query={'id':edge_id, 'canvas_id':canvas_id},
                data=data,
                model_class=ConceptualEdge,
                serializer_class=ConceptualEdgeSerializer
            )
            return Response(result)
        except ValidationError as e:
            # DRF Spectacular will recognize this as a 400 response
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Handle cases where update_serialized_data_by_query might raise 404
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Delete a conceptual edge",
        description=(
            "Permanently removes an edge from the specified canvas. "
            "The operation requires both the edge ID and the parent canvas ID "
            "to ensure structural integrity and security isolation."
        ),
        responses={
            204: OpenApiResponse(description="Edge successfully deleted."),
            404: OpenApiResponse(description="Edge not found in the specified canvas context."),
        },
        tags=['Canvas Edges']
    )
    async def delete(self, request, canvas_id, edge_id):
        try:
            await sync_to_async(delete_instance_by_query)(
                query={'id':edge_id, 'canvas_id':canvas_id},
                model_class=ConceptualEdge
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"detail": "Not found or already deleted."}, status=status.HTTP_404_NOT_FOUND)


class ConceptualEdgeCreateView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create a new conceptual edge",
        description="Creates a relationship between two nodes within a specific canvas context.",
        request=ConceptualEdgeSerializer,
        responses={
            201: ConceptualEdgeSerializer,
            400: None, # or a custom error serializer
        },
        examples=[
            OpenApiExample(
                'Valid Relationship Example',
                summary='A typical evidence-backed connection',
                description='An example showing how to link two nodes with causal evidence and AI rationale.',
                value={
                    "source": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "target": "4bc95f64-5717-4562-b3fc-2c963f66bf21",
                    "sourceHandle": "right",
                    "targetHandle": "left",
                    "label": "Triggers",
                    "type": "TRIGGERS",
                    "evidence": "Observation from clinical trial data in section 4.2",
                    "weight": 1.0,
                    "rationale": "The causal link is inferred from the temporal sequence of events.",
                    "metadata": {
                        "confidence_score": 0.95,
                        "agent_id": "aura-core-v1"
                    }
                },
                request_only=True, # This example is for the request body
            ),
        ],
    )
    async def post(self, request, canvas_id):
        """
        Finalizes the data structure and sends it to the store.
        (Note: Uses sync_to_async for DB compatibility)
        """
        data = request.data

        try:
            # Passing Serializer class directly to the helper
            result = await sync_to_async(create_conceptual_edge)(
                canvas_id,
                data,
                ConceptualEdgeSerializer
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            # DRF Spectacular will recognize this as a 400 response
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


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
