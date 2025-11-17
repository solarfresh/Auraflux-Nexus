from adrf.serializers import Serializer
from rest_framework import serializers


class AssistantPanelSerializer(Serializer):
    """
    Serializes data for the assistant panel.
    """
    related_topics = serializers.ListField(
        child=serializers.CharField(max_length=100)
    )
    next_actions = serializers.ListField(
        child=serializers.CharField(max_length=200)
    )


class SearchResultSerializer(Serializer):
    """
    Serializes the SearchResult model for API responses.
    """
    title = serializers.CharField(max_length=255)
    snippet = serializers.CharField()
    url = serializers.URLField()
    source = serializers.CharField(max_length=100)