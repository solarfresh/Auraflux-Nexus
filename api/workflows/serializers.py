from adrf.serializers import ModelSerializer, Serializer
from rest_framework import serializers

from .models import (ChatHistoryEntry, InitiationPhaseData, TopicKeyword,
                     TopicScopeElement, ReflectionLog)
from .utils import get_resource_suggestion


class ChatEntryHistorySerializer(ModelSerializer):
    """
    Serializer used for validating incoming chat message data from the publisher
    before queuing the persistence task.
    """
    class Meta:
        model = ChatHistoryEntry
        fields = ('id', 'role', 'content', 'name', 'sequence_number', 'timestamp')


class TopicScopeElementSerializer(ModelSerializer):
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


class TopicKeywordSerializer(ModelSerializer):
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


class RefinedTopicSerializer(ModelSerializer):
    """
    Serializer to aggregate all necessary data for the Initiation Phase sidebar.
    Fetches data from InitiationPhaseData and its related models (Keywords, Scope, Reflection).
    """

    keywords = TopicKeywordSerializer(
        source='keywords_list',
        many=True,
        read_only=True
    )
    scope = TopicScopeElementSerializer(
        source='scope_elements_list',
        many=True,
        read_only=True
    )

    latest_reflection = serializers.CharField(
        source='latest_reflection_entry.entry_text',
        read_only=True,
        allow_null=True,
        default=None,
        help_text="The text of the user's latest self-reflection entry."
    )

    resource_suggestion = serializers.SerializerMethodField()

    class Meta:
        model = InitiationPhaseData
        fields = (
            'stability_score',
            'feasibility_status',
            'final_research_question',
            'keywords',
            'scope',
            'latest_reflection',
            'resource_suggestion',
        )

        # stability_score -> stabilityScore
        # final_research_question -> finalQuestion
        # field_mapping = {
        #     'stability_score': 'stabilityScore',
        #     'final_research_question': 'finalQuestion',
        # }

    # def get_field_names(self, declared_fields: Dict[str, Any], info: Dict[str, Any]) -> list:
    #     """Dynamically map database names to frontend prop names."""
    #     fields = super().get_field_names(declared_fields, info)
    #     mapped_fields = [self.Meta.field_mapping.get(f, f) for f in fields]
    #     return mapped_fields

    def get_resource_suggestion(self, obj: InitiationPhaseData) -> str:
        """
        Calculates and returns a resource search suggestion based on the feasibility status.
        """
        return get_resource_suggestion(obj.feasibility_status)


class ReflectionLogSerializer(ModelSerializer):
    """
    Serializer for user reflection logs.
    """
    class Meta:
        model = ReflectionLog
        fields = (
            'id',
            'title',
            'content',
            'status',
            'create_at',
            'updated_at'
        )
        read_only_fields = ('id', 'create_at', 'updated_at')


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
