from adrf.serializers import Serializer
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from rest_framework import serializers


class RefinedTopicSerializer(Serializer):
    """
    A composite serializer representing the full response after topic refinement.
    Matches the 'RefinedTopic' TypeScript interface.
    """
    stabilityScore = serializers.FloatField(source='stability_score', default=0)
    feasibilityStatus = serializers.CharField(source='feasibility_status', default='LOW')
    finalQuestion = serializers.CharField(source='final_research_question', default='')
    keywords = ProcessedKeywordSerializer(many=True, default=[])
    scope = ProcessedScopeSerializer(many=True, source='scope_elements', default=[])
    resourceSuggestion = serializers.CharField(allow_null=True, required=False, source='resource_suggestion', default='')
