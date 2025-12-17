import uuid

from core.constants import ISPStep
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Use the default Django User model for association
User = get_user_model()


class ResearchWorkflow(models.Model):
    """
    Core State Data Structure for managing a user's research workflow,
    tracking Kuhlthau phases, agent outputs, and cost control variables.
    """

    # --- Identification Fields ---
    session_id = models.UUIDField(
        primary_key=True,
        editable=False,
        help_text="Unique identifier for the current research workflow session."
    )
    keywords = GenericRelation(
        "knowledge.TopicKeyword",
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='workflow'
    )
    scope_elements = GenericRelation(
        'knowledge.TopicScopeElement',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='workflow'
    )
    reflection_logs = GenericRelation(
        'workflows.ReflectionLog',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='workflow'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The ID of the user owning this workflow."
    )

    # --- Universal Status & Control ---
    current_stage = models.CharField(
        max_length=50,
        choices=ISPStep.choices,
        default=ISPStep.TOPIC_DEFINITION,
        help_text="Current ISP phase (DEFINITION, EXPLORATION, etc.)."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if the workflow is currently in progress or concluded."
    )

    # --- Metadata ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Workflow: {self.session_id} - Stage: {self.current_stage}"

    class Meta:
        verbose_name = "Research Workflow State"
        verbose_name_plural = "Research Workflow States"


class ChatHistoryEntry(models.Model):
    """
    Stores individual chat messages for a research workflow,
    matching the frontend's ChatMessage interface structure and linked to the
    overall workflow state.
    """

    # Role choices, corresponding to 'user' | 'system' on the frontend
    SENDER_ROLES = (
        ('user', 'User'),
        ('system', 'System/Agent'),
    )

    # Explicitly defining a UUID as the primary key (PK), matching the frontend's 'id: string'
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID) for the chat message, corresponding to the frontend's ID."
    )

    # --- Linkage to Workflow ---
    workflow = models.ForeignKey(
        ResearchWorkflow,
        on_delete=models.CASCADE,
        related_name='chat_history_entries',
        help_text="Foreign key linking the message to the parent research workflow session."
    )

    # --- Core Message Data (Matching Frontend Interface) ---
    # The role of the sender, corresponding to the frontend's 'role'
    role = models.CharField(
        max_length=10,
        choices=SENDER_ROLES,
        help_text="The role of the sender ('user' or 'system')."
    )
    # The actual message content, corresponding to the frontend's 'content'
    content = models.TextField(
        help_text="The text content of the chat message."
    )
    # The specific name or label of the sender, corresponding to the frontend's 'name'
    name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Specific sender identifier (e.g., username, 'Explorer Agent', 'Data Agent')."
    )

    # --- Metadata & Ordering ---
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="The exact time the message was recorded."
    )

    # Ensures the absolute chronological order of the messages
    sequence_number = models.IntegerField(
        help_text="The sequential order of the message within the workflow's history."
    )

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M')}] {self.name} ({self.role}): {self.content[:50]}..."

    class Meta:
        verbose_name = "Chat History Entry"
        verbose_name_plural = "Chat History Entries"
        ordering = ['timestamp', 'sequence_number']


class ReflectionLog(models.Model):
    """
    Stores individual user reflection entries for tracking emotional/cognitive state.
    """

    REFLECTION_STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('COMMITTED', 'Committed'),
    )

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        help_text="Unique identifier for the reflection entry."
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The model type of the owner (Workflows, Resources, etc.)"
    )
    object_id = models.UUIDField(
        help_text="The UUID of the specific owner instance."
    )
    owner = GenericForeignKey('content_type', 'object_id')

    title = models.CharField(
        max_length=255,
        help_text="A short summary title for the log entry."
    )
    content = models.TextField(
        help_text="The detailed reflection content or thought."
    )

    status = models.CharField(
        max_length=10,
        choices=REFLECTION_STATUS_CHOICES,
        default='DRAFT',
        help_text="The current state of the log (DRAFT or COMMITTED)."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="The exact time the log entry was first created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        help_text="The time the log entry was last modified/saved."
    )

    class Meta:
        """Model options."""
        verbose_name = "Reflection Log Entry"
        verbose_name_plural = "Reflection Log Entries"
        # Indexing by update time is useful for fetching the latest drafts/commits
        ordering = ['-updated_at']

    def __str__(self):
        """String representation of the model instance."""
        return f"[{self.status.upper()}] {self.title} ({self.id})"


class InitiationPhaseData(models.Model):
    """
    Data Plane Model: Stores all phase-specific outputs, metrics,
    and control variables exclusive to the INITIATION stage (Kuhlthau 1).
    Modified to store structured data generated by the Topic Refinement Agent.
    """

    # --- Linkage ---
    workflow = models.OneToOneField(
        'ResearchWorkflow', # Use string reference if ResearchWorkflow is defined later
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='initiation_data',
        help_text="One-to-one link to the parent ResearchWorkflow (Control Model)."
    )

    # --- AGENT STRUCTURED OUTPUTS (Core Sidebar Data) ---
    stability_score = models.IntegerField(
        default=0,
        help_text="The Agent's Stability Score [1-10]. Used to derive clarity label and progress visualization."
    )
    feasibility_status = models.CharField(
        max_length=10,
        default='LOW',
        help_text="The Feasibility Status (e.g., LOW, MEDIUM, HIGH) derived from Agent input and structural rules."
    )
    final_research_question = models.TextField(
        default="",
        blank=True,
        help_text="The most refined draft of the research question extracted by the Agent."
    )

    # --- LONG-TERM MEMORY & CONTROL ---
    conversation_summary = models.TextField(
        default="",
        blank=True,
        help_text="The cumulative, incremental summary of the conversation, maintained by the Summarizer Agent (Long-Term Memory)."
    )

    # Anchor for Memory Management and Data Sourcing
    last_analysis_sequence_number = models.IntegerField(
        default=0,
        help_text="The sequence number of the last chat message included in the latest structured analysis (TR Agent) or summary (SUM Agent). Serves as the checkpoint anchor for the next incremental operation."
    )

    # --- Metadata ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Initiation Data for Session: {self.workflow.session_id}"

    class Meta:
        verbose_name = "Initiation Phase Data"
        verbose_name_plural = "Initiation Phase Data"
