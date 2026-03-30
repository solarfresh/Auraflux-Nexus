from adrf.serializers import ModelSerializer, Serializer
from rest_framework import serializers
from projects.models import ChatHistoryEntry, ReflectionLog, ResearchProject


class ChatEntryHistorySerializer(ModelSerializer):
    """
    Serializer used for validating incoming chat message data from the publisher
    before queuing the persistence task.
    """

    sequenceNumber = serializers.IntegerField(source='sequence_number')

    class Meta:
        model = ChatHistoryEntry
        fields = ('id', 'role', 'content', 'name', 'sequenceNumber', 'timestamp')


class ProjectSerialize(ModelSerializer):
    currentStage = serializers.CharField(source='current_stage')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ResearchProject
        fields = (
            'id',
            'name',
            'description',
            'status',
            'currentStage',
            'createdAt',
            'updatedAt'
        )
        read_only_fields = ('id', 'createdAt', 'updatedAt')


class ReflectionLogSerializer(ModelSerializer):
    """
    Serializer for user reflection logs.
    """
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ReflectionLog
        fields = (
            'id',
            'title',
            'content',
            'status',
            'createdAt',
            'updatedAt'
        )
        read_only_fields = ('id', 'createdAt', 'updatedAt')


class ProjectChatInputRequestSerializer(Serializer):
    user_message = serializers.CharField(
        help_text="The chat message input from the user."
    )
    ea_agent_role_name = serializers.CharField(
        help_text="The role name of the Explorer Agent to handle the chat input.",
        default="ExplorerAgent"
    )


class ProjectChatInputResponseSerializer(Serializer):
    status = serializers.CharField(
        help_text="Status of the chat input processing."
    )
    message = serializers.CharField(
        help_text="Detailed message regarding the processing outcome."
    )

