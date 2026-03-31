from adrf.serializers import ModelSerializer, Serializer
from rest_framework import serializers
from agents.models import AgentRoleConfig


class AgentConfigSerializer(ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    systemPrompt = serializers.CharField(source='system_prompt')
    promptTemplate = serializers.CharField(source='prompt_template')
    templateVariables = serializers.JSONField(source='template_variables')
    outputSchema = serializers.JSONField(source='output_schema')

    class Meta:
        model = AgentRoleConfig
        fields = (
            'id',
            'createdAt',
            'updatedAt',
            'name',
            'systemPrompt',
            'promptTemplate',
            'templateVariables',
            'outputSchema'
        )
        read_only_fields = ('id', 'createdAt', 'updatedAt')
