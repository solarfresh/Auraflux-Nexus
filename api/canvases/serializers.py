from adrf.serializers import ModelSerializer, Serializer
from canvases.constants import EdgeType, NodeHandle, NodeType
from canvases.models import ConceptualEdge, ConceptualNode
from core.constants import EntityStatus
from rest_framework import serializers


class PositionSerializer(Serializer):
    x = serializers.FloatField()
    y = serializers.FloatField()


class ConceptualEdgeSerializer(ModelSerializer):
    type = serializers.ChoiceField(choices=EdgeType.choices, source='edge_type', default=EdgeType.REF)
    source = serializers.UUIDField(source='source_id', read_only=True)
    sourceHandle = serializers.ChoiceField(choices=NodeHandle.choices, source='source_handle')
    target = serializers.UUIDField(source='target_id', read_only=True)
    targetHandle = serializers.ChoiceField(choices=NodeHandle.choices, source='target_handle')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ConceptualEdge
        fields = [
            'id',
            'source',
            'sourceHandle',
            'target',
            'targetHandle',
            'label',
            'type',
            'status',
            'evidence',
            'weight',
            'rationale',
            'metadata',
            'createdAt',
            'updatedAt'
        ]


class ConceptualNodeSerializer(ModelSerializer):
    # --- UI & Layout ---
    position = PositionSerializer(required=False)
    status = serializers.ChoiceField(choices=EntityStatus.choices, required=False)
    type = serializers.ChoiceField(choices=NodeType.choices, source='node_type')

    # --- Knowledge & Anti-Hallucination ---
    sourceRef = serializers.CharField(source='source_ref', allow_blank=True, required=False)
    anchorId = serializers.PrimaryKeyRelatedField(
        source='anchor',
        queryset=ConceptualNode.objects.all(),
        required=False,
        allow_null=True
    )

    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ConceptualNode
        fields = [
            'id',
            'label',
            'type',
            'position',
            'groundedness',
            'solidity',
            'content',
            'sourceRef',
            'rationale',
            'anchorId',
            'status',
            'createdAt',
            'updatedAt'
        ]


class ConceptualGraphSerializer(serializers.Serializer):
    """
    Represents the current state (ground truth) of the canvas layout.
    """
    nodes = serializers.DictField(
        child=ConceptualNodeSerializer(),
        default=dict,
        help_text="A mapping of unique keys to node data objects."
    )
    edges = serializers.ListField(
        child=ConceptualEdgeSerializer(),
        default=list,
        help_text="A collection of connection parameters between nodes."
    )


class RecommendedConceptualNodeSerializer(Serializer):
    id = serializers.UUIDField(
        help_text="Unique identifier for the node."
    )
    label = serializers.CharField(
        help_text="Display text or name associated with the node."
    )
    type = serializers.ChoiceField(choices=NodeType.choices, source='node_type')
    anchor_id = serializers.UUIDField(
        help_text="The reference ID used to set positional constraints."
    )
    rationale = serializers.CharField(
        help_text="The logic or reasoning behind the node's placement or selection."
    )
