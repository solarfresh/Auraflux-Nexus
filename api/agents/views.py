import logging

from adrf.views import APIView
from agents.models import AgentRoleConfig, ModelProvider
from agents.serializers import AgentConfigSerializer, ModelProviderSerializer
from asgiref.sync import sync_to_async
from core.utils import (create_serialized_data, get_serialized_data,
                        get_serialized_data_by_id,
                        update_serialized_data_by_id)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class AgentConfigView(APIView):

    permission_classes = [IsAuthenticated]

    async def get(self, request):
        user = request.user

        data = await sync_to_async(get_serialized_data)({'user_id': user.id}, AgentRoleConfig, AgentConfigSerializer, many=True)
        return Response(data, status=status.HTTP_200_OK)


class AgentConfigDetailView(APIView):

    permission_classes = [IsAuthenticated]

    async def get(self, request, agent_id):
        data = await sync_to_async(get_serialized_data_by_id)(agent_id, AgentRoleConfig, AgentConfigSerializer)
        return Response(data, status=status.HTTP_200_OK)

    async def put(self, request, agent_id):
        request_data = request.data
        try:
            data = await sync_to_async(update_serialized_data_by_id)(agent_id, request_data, AgentRoleConfig, AgentConfigSerializer)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class ModelProviderView(APIView):

    permission_classes = [IsAuthenticated]

    async def get(self, request):
        user = request.user

        data = await sync_to_async(get_serialized_data)({'user_id': user.id}, ModelProvider, ModelProviderSerializer, many=True)
        return Response(data, status=status.HTTP_200_OK)

    async def post(self, request):
        user = request.user
        request_data = request.data
        request_data['user_id'] = user.id
        try:
            data = await sync_to_async(create_serialized_data)(request_data, ModelProviderSerializer)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class ModelProviderDetailView(APIView):

    permission_classes = [IsAuthenticated]

    async def get(self, request, provider_id):
        data = await sync_to_async(get_serialized_data_by_id)(provider_id, ModelProvider, ModelProviderSerializer)
        return Response(data, status=status.HTTP_200_OK)

    async def put(self, request, provider_id):
        request_data = request.data
        try:
            data = await sync_to_async(update_serialized_data_by_id)(provider_id, request_data, ModelProvider, ModelProviderSerializer)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
