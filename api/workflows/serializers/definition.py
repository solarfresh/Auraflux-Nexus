from adrf.serializers import Serializer
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from rest_framework import serializers


class RefinedTopicSerializer(Serializer):
    """
    A composite serializer representing the full response after topic refinement.
    Matches the 'APIRefinedTopic' TypeScript interface.
    """
    stabilityScore = serializers.FloatField()
    feasibilityStatus = serializers.CharField()
    finalResearchQuestion = serializers.CharField()
    keywords = ProcessedKeywordSerializer(many=True)
    scope = ProcessedScopeSerializer(many=True)
    resourceSuggestion = serializers.CharField(allow_null=True, required=False)
