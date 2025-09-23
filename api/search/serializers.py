from rest_framework import serializers
from search.models import SearchResult


class SearchResultSerializer(serializers.ModelSerializer):
    """
    Serializes the SearchResult model for API responses.
    """
    class Meta:
        model = SearchResult
        fields = ['title', 'description', 'link', 'source']