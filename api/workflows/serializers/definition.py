from adrf.serializers import Serializer
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from rest_framework import serializers


class RefinedTopicSerializer(Serializer):
    """
    A composite serializer representing the full response after topic refinement.
    Matches the 'RefinedTopic' TypeScript interface.
    """
    stabilityScore = serializers.FloatField(source='stability_score')
    feasibilityStatus = serializers.CharField(source='feasibility_status')
    finalResearchQuestion = serializers.CharField(source='final_research_question')
    keywords = ProcessedKeywordSerializer(many=True)
    scope = ProcessedScopeSerializer(many=True, source='scope_elements')
    resourceSuggestion = serializers.CharField(allow_null=True, required=False, source='resource_suggestion')
