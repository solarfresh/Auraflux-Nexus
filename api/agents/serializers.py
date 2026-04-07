from adrf.serializers import ModelSerializer, Serializer
from rest_framework import serializers
from agents.models import AgentRoleConfig, ModelProvider


class AgentConfigSerializer(ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    systemPrompt = serializers.CharField(source='system_prompt')
    promptTemplate = serializers.CharField(source='prompt_template')
    templateVariables = serializers.JSONField(source='template_variables')
    outputSchema = serializers.JSONField(source='output_schema')
    llmParameters = serializers.JSONField(source='llm_parameters')

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
            'outputSchema',
            'llmParameters'
        )
        read_only_fields = ('id', 'createdAt', 'updatedAt')


class ModelProviderSerializer(ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    providerType = serializers.CharField(source='provider_type')
    baseUrl = serializers.URLField(source='base_url', required=False)
    lastVerifiedAt = serializers.DateTimeField(source='last_verified_at', read_only=True)
    apiKeyFingerprint = serializers.ReadOnlyField(source='api_key_fingerprint')
    apiKey = serializers.CharField(
        source='api_key',
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="The raw API key to be encrypted and stored."
    )

    class Meta:
        model = ModelProvider
        fields = [
            'id', 'name', 'providerType', 'apiKey', 'apiKeyFingerprint',
            'baseUrl', 'status', 'lastVerifiedAt',
            'createdAt', 'updatedAt'
        ]

    def create(self, validated_data):
        api_key = validated_data.pop('api_key', None)
        instance = ModelProvider.objects.create(**validated_data)

        if api_key:
            instance.set_api_key(api_key)
            instance.save()

        return instance

    def update(self, instance, validated_data):
        api_key = validated_data.pop('api_key', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if api_key:
            instance.set_api_key(api_key)

        instance.save()
        return instance