from adrf.serializers import ModelSerializer, Serializer
from rest_framework import serializers

from .models import ChatHistoryEntry, UserReflectionLog, TopicKeyword, TopicScopeElement


class ChatEntryHistorySerializer(ModelSerializer):
    """
    Serializer used for validating incoming chat message data from the publisher
    before queuing the persistence task.
    """
    class Meta:
        model = ChatHistoryEntry
        fields = ('id', 'role', 'content', 'name', 'sequence_number', 'timestamp')


class TopicScopeElementSerializer(serializers.ModelSerializer):
    """
    Serializer for TopicScopeElement model.
    Used to represent individual scope components (label and value)
    and their current status (LOCKED or DRAFT) for the Initiation Phase sidebar display.
    """

    class Meta:
        model = TopicScopeElement
        fields = (
            'id',
            'label',          # e.g., 'Timeframe', 'Geographical Focus'
            'value',          # e.g., '2015-2025', 'Brazil and Vietnam'
            'status',         # The status (LOCKED, DRAFT, DISCARDED)
            'updated_at'
        )
        read_only_fields = ('id', 'updated_at')


class TopicKeywordSerializer(serializers.ModelSerializer):
    """
    Serializer for TopicKeyword model.
    Used to represent individual keywords and their current status
    (LOCKED or DRAFT) for the Initiation Phase sidebar display.
    """

    class Meta:
        model = TopicKeyword
        fields = (
            'id',
            'text',
            'status',
            'confidence_score',
            'updated_at'
        )
        read_only_fields = ('id', 'confidence_score', 'updated_at')


class UserReflectionLogSerializer(ModelSerializer):
    """
    Serializer for user reflection logs.
    """
    class Meta:
        model = UserReflectionLog
        fields = ('id', 'user_id', 'reflection_text', 'created_at')


class WorkflowChatInputRequestSerializer(Serializer):
    user_message = serializers.CharField(
        help_text="The chat message input from the user."
    )
    ea_agent_role_name = serializers.CharField(
        help_text="The role name of the Explorer Agent to handle the chat input.",
        default="ExplorerAgent"
    )

class WorkflowChatInputResponseSerializer(Serializer):
    status = serializers.CharField(
        help_text="Status of the chat input processing."
    )
    message = serializers.CharField(
        help_text="Detailed message regarding the processing outcome."
    )
