from adrf.serializers import ModelSerializer, Serializer
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from rest_framework import serializers
from workflows.models import InitiationPhaseData


class InitiationPhaseDataSerializer(ModelSerializer):
    """
    Serializer for InitiationPhaseData model.
    Used to represent the overall state and key attributes of the Initiation Phase.
    """
    class Meta:
        model = InitiationPhaseData
        fields = (
            'workflow_id',
            'stability_score',
            'feasibility_status',
            'final_research_question',
            'conversation_summary',
            'last_analysis_sequence_number',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('workflow_id', 'created_at', 'updated_at')


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
