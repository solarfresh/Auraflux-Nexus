from adrf.serializers import ModelSerializer, Serializer
from canvases.serializers import ConceptualNodeSerializer
from rest_framework import serializers
from projects.models import ExplorationPhaseData


class ExplorationPhaseDataSerializer(ModelSerializer):
    """
    Serializer for ExplorationPhaseData model.
    Used to represent the overall state and key attributes of the Exploration Phase.
    """
    projectId = serializers.UUIDField(source='project_id', read_only=True)
    stabilityScore = serializers.FloatField(source='stability_score', default=0)
    finalQuestion = serializers.CharField(source='final_research_question', default='')
    activeCanvasId = serializers.UUIDField(source='activated_canvas_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ExplorationPhaseData
        fields = (
            'projectId',
            'stabilityScore',
            'finalQuestion',
            'createdAt',
            'updatedAt'
        )
        read_only_fields = ('projectId', 'createdAt', 'updatedAt')


class SidebarRegistryInfoSerializer(Serializer):
    """
    Serializer for the sidebar registry information related to the Exploration Phase.
    This includes the stability score, final research question, activated canvas ID, and the list of conceptual nodes.
    """
    stabilityScore = serializers.FloatField(source='stability_score', default=0)
    finalQuestion = serializers.CharField(source='final_research_question', default='')
    activeCanvasId = serializers.UUIDField(source='activated_canvas_id', default='')
    nodes = ConceptualNodeSerializer(many=True, default=[])
