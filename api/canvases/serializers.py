from adrf.serializers import ModelSerializer
from canvases.constants import NodeType
from canvases.models import ConceptualNode
from rest_framework import serializers


class ConceptualNodeSerializer(ModelSerializer):
    nodeType = serializers.ChoiceField(choices=NodeType.choices, source='node_type')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ConceptualNode
        fields = [
            'id',
            'label',
            'nodeType',
            'groundedness',
            'solidity',
            'createdAt',
            'updatedAt'
        ]
