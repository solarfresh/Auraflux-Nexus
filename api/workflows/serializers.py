from adrf.serializers import Serializer
from rest_framework import serializers


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
