from adrf.serializers import ModelSerializer
from rest_framework import serializers
from projects.models import ExplorationPhaseData


class ExplorationPhaseDataSerializer(ModelSerializer):
    """
    Serializer for ExplorationPhaseData model.
    Used to represent the overall state and key attributes of the Exploration Phase.
    """
    projectId = serializers.UUIDField(source='project_id', read_only=True)
    activeCanvasId = serializers.UUIDField(source='active_canvas_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ExplorationPhaseData
        fields = (
            'projectId',
            'activeCanvasId',
            'createdAt',
            'updatedAt'
        )
        read_only_fields = ('projectId', 'createdAt', 'updatedAt')
