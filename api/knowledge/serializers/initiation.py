from adrf.serializers import ModelSerializer, Serializer
from core.constants import WorkflowState
from knowledge.models import TopicKeyword, TopicScopeElement
from rest_framework import serializers


class ProcessedKeywordSerializer(ModelSerializer):
    """
    Maps TopicKeyword to the ProcessedKeyword frontend interface.
    Renames 'status' to 'workflowState' and ensures camelCase.
    """
    workflowState = serializers.ChoiceField(choices=WorkflowState.choices, source='status')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = TopicKeyword
        fields = [
            'id',
            'label',
            'importance_weight',
            'is_core',
            'semantic_category',
            'workflowState',
            'createdAt',
            'updatedAt'
        ]


class ProcessedScopeSerializer(ModelSerializer):
    """
    Maps TopicScopeElement to the ProcessedScope frontend interface.
    Ensures 'rationale' and 'boundary_type' match frontend expectations.
    """
    workflowState = serializers.ChoiceField(choices=WorkflowState.choices, source='status')
    boundaryType = serializers.CharField(source='boundary_type')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = TopicScopeElement
        fields = [
            'id',
            'label',
            'boundaryType',
            'rationale',
            'workflowState',
            'createdAt',
            'updatedAt'
        ]


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

    # Note: This is a read-only data transfer object (DTO) used by the Service Layer