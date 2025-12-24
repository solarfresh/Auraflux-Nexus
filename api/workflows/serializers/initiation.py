from adrf.serializers import ModelSerializer
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
