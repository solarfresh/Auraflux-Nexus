from adrf.serializers import ModelSerializer, Serializer
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from rest_framework import serializers


class SidebarRegistryInfoSerializer(Serializer):
    """
    """
    stabilityScore = serializers.FloatField(source='stability_score', default=0)
    finalQuestion = serializers.CharField(source='final_research_question', default='')
    keywords = ProcessedKeywordSerializer(many=True, default=[])
    scope = ProcessedScopeSerializer(many=True, source='scope_elements', default=[])
