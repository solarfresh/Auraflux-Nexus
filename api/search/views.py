import json

from adrf.views import APIView
from django.apps import apps
from rest_framework.response import Response
from search.serializers import AssistantPanelSerializer, SearchResultSerializer


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
    async def post(self, request, *args, **kwargs):
        query = request.data.get('query', '').strip()

        search_app_config = apps.get_app_config('search')
        google_search_tool = getattr(search_app_config, 'google_search_tool', None)
        if not google_search_tool:
            raise AttributeError("google_search_tool not found in search app configuration")

        search_results_string = await google_search_tool.run(query=query)
        search_results = json.loads(search_results_string)

        serializer = SearchResultSerializer(data=search_results, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
