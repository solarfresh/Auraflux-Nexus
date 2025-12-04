from adrf.serializers import ModelSerializer, Serializer
from rest_framework import serializers

from .models import ChatHistoryEntry


class ChatEntryHistorySerializer(ModelSerializer):
    """
    Serializer used for validating incoming chat message data from the publisher
    before queuing the persistence task.
    """
    class Meta:
        model = ChatHistoryEntry
        fields = ('id', 'role', 'content', 'name', 'sequence_number', 'timestamp')


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
