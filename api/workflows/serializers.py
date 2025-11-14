from adrf.serializers import ModelSerializer
from rest_framework import serializers

from .models import KnowledgeSource, WorkflowState


class KnowledgeSourceSerializer(ModelSerializer):
    """
    Serializer for the KnowledgeSource model, used to represent the list
    of locked search results nested within the WorkflowState.
    """
    class Meta:
        model = KnowledgeSource
        fields = (
            'id',
            'query',
            'title',
            'snippet',
            'url',
            'source',
            'locked_at',
        )
        read_only_fields = fields # Sources are typically read-only once saved/locked


class WorkflowStateSerializer(serializers.ModelSerializer):
    """
    Serializer for the WorkflowState model, providing the complete
    application state to the frontend.
    """
    # Nested field for the locked search results (reverse relationship)
    # The 'knowledge_sources' name must match the related_name in the ForeignKey field
    knowledge_sources = KnowledgeSourceSerializer(many=True, read_only=True)

    # We expose the updated_at timestamp to let the frontend know the data's freshness
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = WorkflowState
        fields = (
            'current_step',
            'scope_data',
            'analysis_data',
            'knowledge_sources',  # Nested sources list
            'updated_at',
        )
        read_only_fields = ('current_step', 'updated_at') # Most fields are read-only on GET
