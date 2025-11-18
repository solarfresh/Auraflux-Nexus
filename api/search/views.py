import json

from adrf.views import APIView
from asgiref.sync import sync_to_async
from django.apps import apps
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from search.serializers import AssistantPanelSerializer, SearchResultSerializer

from .utils import get_user_cache_key


class AssistantPanelView(APIView):
    """
    Handles requests for the assistant panel data.
    """
    async def post(self, request, *args, **kwargs):
        query = request.data.get('query', '').lower()

        # Mock data for the assistant panel
        assistant_data_map = {
            '創業': {
                'related_topics': ['Business Plan', 'Venture Capital', 'Marketing Strategy'],
                'next_actions': [
                    'Research different business models for your idea.',
                    'Look for startup incubators in your area.',
                    'Find government grants for new businesses.'
                ],
            },
            '幼兒成長': {
                'related_topics': ['Sensory Play', 'Child Psychology', 'Early Education'],
                'next_actions': [
                    'Find parenting workshops near you.',
                    'Download our guide on developmental milestones.',
                    'Connect with other parents in our community forums.'
                ],
            },
            'default': {
                'related_topics': ['Trending Articles', 'Community Forums'],
                'next_actions': ['Start a new search', 'Browse popular topics']
            }
        }

        # Simple keyword matching to provide a response
        data = assistant_data_map.get('default')
        if '創業' in query:
            data = assistant_data_map['創業']
        elif '幼兒' in query: # Use '幼兒' for broader matching
            data = assistant_data_map['幼兒成長']

        serializer = AssistantPanelSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class SearchView(APIView):
    """
    Handles search requests and returns mock data based on the query.
    """
    permission_classes = [IsAuthenticated]

    async def post(self, request, *args, **kwargs):
        user = request.user
        query = request.data.get('query', '').strip()

        if not query:
            return Response({"error": "Search query is required."}, status=400)

        cache_key = get_user_cache_key(user.id)

        # Check Cache for Existing Results
        # Cache access is synchronous, so we must wrap it.
        cached_data = await sync_to_async(cache.get)(cache_key)

        if cached_data:
            # Check if the cached query matches the current request's query
            if cached_data.get('query') == query:
                # Return cached data if the query hasn't changed
                return Response(cached_data.get('results'))

        search_app_config = apps.get_app_config('search')
        google_search_tool = getattr(search_app_config, 'google_search_tool', None)
        if not google_search_tool:
            raise AttributeError("google_search_tool not found in search app configuration")

        search_results_string = await google_search_tool.run(query=query)
        search_results = json.loads(search_results_string)

        serializer = SearchResultSerializer(data=search_results, many=True)
        serializer.is_valid(raise_exception=True)
        validated_results = serializer.validated_data

        data_to_cache = {
            'query': query,
            'results': validated_results,
        }
        await sync_to_async(cache.set)(cache_key, data_to_cache)

        return Response(validated_results)
