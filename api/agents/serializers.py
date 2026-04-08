from adrf.serializers import ModelSerializer, Serializer
from rest_framework import serializers
from agents.models import AgentRoleConfig, ModelProvider, ModelFamilies


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


class ModelFamiliesSerializer(ModelSerializer):
    class Meta:
        model = ModelFamilies
        fields = '__all__'


class ModelProviderSerializer(ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    type = serializers.CharField(source='provider_type')
    baseUrl = serializers.URLField(source='base_url', required=False, allow_blank=True)
    latencyMs = serializers.IntegerField(source='latency_ms')
    lastVerifiedAt = serializers.DateTimeField(source='last_verified_at', read_only=True)
    apiKeyFingerprint = serializers.ReadOnlyField(source='api_key_fingerprint')
    apiKey = serializers.CharField(
        source='api_key',
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="The raw API key to be encrypted and stored."
    )
    supportedFamilies = ModelFamiliesSerializer(source='supported_families', many=True, read_only=True)
    activeAgentCount = serializers.IntegerField(source='active_agent_count', read_only=True)

    class Meta:
        model = ModelProvider
        fields = [
            'id', 'name', 'type', 'apiKey', 'apiKeyFingerprint',
            'baseUrl', 'status', 'user', 'latencyMs', 'lastVerifiedAt',
            'supportedFamilies', 'activeAgentCount', 'createdAt', 'updatedAt'
        ]
        extra_kwargs = {
            'user': {'write_only': True},
        }

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