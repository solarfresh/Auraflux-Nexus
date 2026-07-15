import logging
from adrf.serializers import ModelSerializer, Serializer
from canvases.constants import EdgeType, NodeHandle, NodeType
from canvases.models import CanvasNodeRelation, ConceptualEdge, ConceptualNode
from core.constants import EntityStatus
from rest_framework import serializers

logger = logging.getLogger(__name__)


class PositionSerializer(Serializer):
    x = serializers.FloatField()
    y = serializers.FloatField()


class ConceptualEdgeSerializer(ModelSerializer):
    type = serializers.ChoiceField(choices=EdgeType.choices, source='edge_type', default=EdgeType.REF)
    source = serializers.UUIDField(source='source_id')
    sourceHandle = serializers.ChoiceField(choices=NodeHandle.choices, source='source_handle')
    target = serializers.UUIDField(source='target_id')
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
    status = serializers.ChoiceField(choices=EntityStatus.choices, required=False)
    type = serializers.ChoiceField(choices=NodeType.choices, source='node_type')

    # --- Knowledge & Anti-Hallucination ---
    sourceRef = serializers.CharField(source='source_ref', allow_blank=True, allow_null=True, required=False)

    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ConceptualNode
        fields = [
            'id',
            'label',
            'type',
            'content',
            'sourceRef',
            'rationale',
            'status',
            'createdAt',
            'updatedAt'
        ]


class CanvasNodeRelationSerializer(serializers.ModelSerializer):
    node_id = serializers.PrimaryKeyRelatedField(
        queryset=ConceptualNode.objects.all(),
        source='node'
    )
    position = PositionSerializer(required=False)
    rationale = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = CanvasNodeRelation
        fields = ['node_id', 'status', 'rationale', 'position']

    def validate(self, attrs):
        if 'position' in attrs:
            position_data = attrs.pop('position', {})
            attrs['x'] = position_data.get('x')
            attrs['y'] = position_data.get('y')
        return attrs

    def create(self, validated_data):
        validated_data['canvas_id'] = self.context['canvas_id']
        return super().create(validated_data)

    def to_representation(self, instance):
        return {
            'id': instance.node.id,
            'label': instance.node.label,
            'type': instance.node.node_type,
            'content': instance.node.content,
            'sourceRef': instance.node.source_ref,
            'createdAt': instance.node.created_at,
            'updatedAt': instance.node.updated_at,
            'position': {
                'x': instance.x,
                'y': instance.y
            },
            'status': instance.status,
            'rationale': instance.rationale,
        }


class ConceptualGraphSerializer(serializers.Serializer):
    """
    Represents the current state (ground truth) of the canvas layout.
    """
    canvasId = serializers.UUIDField(
        source='canvas_id',
        help_text="Unique identifier for the canvas."
    )
    nodes = serializers.DictField(
        child=CanvasNodeRelationSerializer(),
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
