from adrf.serializers import ModelSerializer, Serializer
from knowledge.serializers import (ProcessedKeywordSerializer,
                                   ProcessedScopeSerializer)
from rest_framework import serializers
from projects.models import ConsultationPhaseData


class ConsultationPhaseDataSerializer(ModelSerializer):
    """
    Serializer for ConsultationPhaseData model.
    Used to represent the overall state and key attributes of the Consultation Phase.
    """
    class Meta:
        model = ConsultationPhaseData
        fields = (
            'project_id',
            'stability_score',
            'feasibility_status',
            'final_research_question',
            'conversation_summary',
            'last_analysis_sequence_number',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('project_id', 'created_at', 'updated_at')
