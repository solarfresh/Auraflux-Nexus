import logging

from adrf.views import APIView
from asgiref.sync import sync_to_async
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from knowledge.models import TopicKeyword, TopicScopeElement
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .utils import update_topic_keyword_by_id, update_topic_scope_element_by_id

logger = logging.getLogger(__name__)


class TopicKeywordView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update an Existing Topic Keyword",
        description=(
            "Updates the text and status of an existing Topic Keyword identified by keyword_id."
        ),
        parameters=[
            OpenApiParameter(
                name="keyword_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the topic keyword.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        request=ProcessedKeywordSerializer,
        responses={
            200: ProcessedKeywordSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def put(self, request, keyword_id):
        keyword_text = request.data.get('text')
        keyword_status = request.data.get('status', None)
        if not keyword_text:
            return Response(
                {"detail": "text is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = await sync_to_async(update_topic_keyword_by_id)(keyword_id, keyword_text, keyword_status, serializer_class=ProcessedKeywordSerializer)
        except TopicKeyword.DoesNotExist:
            return Response(
                {"detail": f"Keyword '{keyword_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)


class TopicScopeElementView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update an Existing Topic Scope Element",
        description=(
            "Updates the text and status of an existing Topic Scope Element identified by scope_id."
        ),
        parameters=[
            OpenApiParameter(
                name="scope_id",
                location=OpenApiParameter.PATH,
                description="Unique identifier for the topic scope element.",
                required=True,
                type=OpenApiTypes.UUID,
            )
        ],
        request=ProcessedScopeSerializer,
        responses={
            200: ProcessedScopeSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        }
    )
    async def put(self, request, scope_id):
        scope_label = request.data.get('label')
        scope_value = request.data.get('value')
        scope_status = request.data.get('status', None)
        if not scope_label:
            return Response(
                {"detail": "label is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not scope_value:
            return Response(
                {"detail": "value is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = await sync_to_async(update_topic_scope_element_by_id)(scope_id, scope_value, scope_label, scope_status, serializer_class=ProcessedScopeSerializer)
        except TopicScopeElement.DoesNotExist:
            return Response(
                {"detail": f"Scope Element '{scope_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)
