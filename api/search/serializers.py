from rest_framework import serializers
from search.models import SearchResult


class AssistantPanelSerializer(serializers.Serializer):
    """
    Serializes data for the assistant panel.
    """
    related_topics = serializers.ListField(
        child=serializers.CharField(max_length=100)
    )
    next_actions = serializers.ListField(
        child=serializers.CharField(max_length=200)
    )


class SearchResultSerializer(serializers.ModelSerializer):
    """
    Serializes the SearchResult model for API responses.
    """
    class Meta:
        model = SearchResult
        fields = ['title', 'description', 'link', 'source']