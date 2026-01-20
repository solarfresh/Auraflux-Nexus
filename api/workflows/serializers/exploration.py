from adrf.serializers import ModelSerializer, Serializer
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from rest_framework import serializers
from workflows.models import ExplorationPhaseData


class ExplorationPhaseDataSerializer(ModelSerializer):
    """
    Serializer for ExplorationPhaseData model.
    Used to represent the overall state and key attributes of the Exploration Phase.
    """
    workflowId = serializers.UUIDField(source='workflow_id', read_only=True)
    stabilityScore = serializers.FloatField(source='stability_score', default=0)
    finalQuestion = serializers.CharField(source='final_research_question', default='')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ExplorationPhaseData
        fields = (
            'workflowId',
            'stabilityScore',
            'finalQuestion',
            'createdAt',
            'updatedAt'
        )
        read_only_fields = ('workflowId', 'createdAt', 'updatedAt')


class SidebarRegistryInfoSerializer(Serializer):
    """
    """
    stabilityScore = serializers.FloatField(source='stability_score', default=0)
    finalQuestion = serializers.CharField(source='final_research_question', default='')
    keywords = ProcessedKeywordSerializer(many=True, default=[])
    scope = ProcessedScopeSerializer(many=True, source='scope_elements', default=[])
