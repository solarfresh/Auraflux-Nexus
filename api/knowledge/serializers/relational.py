from adrf.serializers import ModelSerializer
from core.constants import EntityStatus
from knowledge.models import TopicKeyword, TopicScopeElement
from rest_framework import serializers


class ProcessedKeywordSerializer(ModelSerializer):
    """
    Maps TopicKeyword to the ProcessedKeyword frontend interface.
    Renames 'status' to 'workflowState' and ensures camelCase.
    """
    importanceWeight = serializers.FloatField(source='importance_weight')
    isCore = serializers.BooleanField(source='is_core')
    entityStatus = serializers.ChoiceField(choices=EntityStatus.choices, source='status')
    semanticCategory = serializers.CharField(source='semantic_category')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = TopicKeyword
        fields = [
            'id',
            'label',
            'importanceWeight',
            'isCore',
            'semanticCategory',
            'entityStatus',
            'createdAt',
            'updatedAt'
        ]


class ProcessedScopeSerializer(ModelSerializer):
    """
    Maps TopicScopeElement to the ProcessedScope frontend interface.
    Ensures 'rationale' and 'boundary_type' match frontend expectations.
    """
    entityStatus = serializers.ChoiceField(choices=EntityStatus.choices, source='status')
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
            'entityStatus',
            'createdAt',
            'updatedAt'
        ]
