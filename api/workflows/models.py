import uuid

from django.contrib.auth import get_user_model
from django.db import models

# Use the default Django User model for association
User = get_user_model()


class KuhlthauStage(models.TextChoices):
    # [DB Value] = [Constant Name], [Human Readable Label]
    TOPIC_DEFINITION_LOCKIN = 'INITIATION', '1. Topic Definition & Lock-in (Uncertainty → Optimism)'
    EXPLORATION = 'EXPLORATION', '2. Exploration (Confusion/Doubt)'
    FORMULATION = 'FORMULATION', '3. Formulation (Clarity)'
    COLLECTION = 'COLLECTION', '4. Collection (Satisfaction)'
    PRESENTATION = 'PRESENTATION', '5. Presentation (Closure)'

    @classmethod
    def get_emotional_state(cls, stage):
        if stage == cls.TOPIC_DEFINITION_LOCKIN:
            return 'Uncertainty'
        return 'N/A'


class ResearchWorkflowState(models.Model):
    """
    Core State Data Structure for managing a user's research workflow,
    tracking Kuhlthau phases, agent outputs, and cost control variables.
    """

    # Define choices for the Kuhlthau ISP stages
    KUHLTHAU_STAGES = (
        # Merges original INITIATION (1) and SELECTION (2).
        # This phase handles the entire process from vague concept to locked research question,
        # guided by the Stability Score.
        ('TOPIC_DEFINITION_LOCKIN', '1. Topic Definition & Lock-in (Uncertainty → Optimism)'),

        # Corresponds to original ISP stage 3. Focus on sifting information and evaluation.
        ('EXPLORATION', '2. Exploration (Confusion/Doubt)'),

        # Corresponds to original ISP stage 4. Focus on synthesizing information into arguments.
        ('FORMULATION', '3. Formulation (Clarity)'),

        # Corresponds to original ISP stage 5. Focus on precise evidence gathering.
        ('COLLECTION', '4. Collection (Confidence)'),

        # Corresponds to original ISP stage 6. Focus on finalizing and outputting the report.
        ('PRESENTATION', '5. Presentation (Satisfaction/Closure)'),
    )

    # --- Identification Fields ---    # --- Identification & Linkage Fields ---
    session_id = models.UUIDField(
        primary_key=True,
        editable=False,
        help_text="Unique identifier for the current research workflow session."
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The ID of the user owning this workflow."
    )

    # --- Universal Status & Control ---
    current_stage = models.CharField(
        max_length=50,
        choices=KuhlthauStage.choices,
        default=KuhlthauStage.TOPIC_DEFINITION_LOCKIN,
        help_text="Current Kuhlthau phase (INITIATION, SELECTION, etc.)."
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
    workflow_state = models.ForeignKey(
        ResearchWorkflowState,
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

    workflow_state = models.ForeignKey(
        ResearchWorkflowState,
        on_delete=models.CASCADE,
        related_name='reflection_log_entries',
        help_text="Foreign key linking the reflection logs to the parent research workflow session."
    )

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
    workflow_state = models.OneToOneField(
        'ResearchWorkflowState', # Use string reference if ResearchWorkflowState is defined later
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='initiation_data',
        help_text="One-to-one link to the parent ResearchWorkflowState (Control Model)."
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
        return f"Initiation Data for Session: {self.workflow_state.session_id}"

    class Meta:
        verbose_name = "Initiation Phase Data"
        verbose_name_plural = "Initiation Phase Data"


class TopicKeyword(models.Model):
    """
    Stores individual keywords related to the topic for the Initiation Phase.
    """

    KEYWORD_STATUS_CHOICES = [
        ('LOCKED', 'Locked (Committed and Finalized)'),
        ('USER_DRAFT', 'User Draft (Created by User, Pending Review)'),
        ('AI_EXTRACTED', 'AI Extracted (Captured from Chat, Needs Review)'),
        ('ON_HOLD', 'On Hold (Excluded from Current Topic)'),
    ]

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        help_text="Unique identifier for the keyword entry."
    )

    workflow_state = models.ForeignKey(
        ResearchWorkflowState,
        on_delete=models.CASCADE,
        related_name='keywords_list',
        help_text="Foreign key linking the keyword to the parent research workflow session."
    )

    text = models.CharField(
        max_length=255,
        help_text="The keyword or key phrase itself."
    )

    status = models.CharField(
        max_length=20,
        choices=KEYWORD_STATUS_CHOICES,
        default='USER_DRAFT',
        help_text="The current status of the keyword (LOCKED, DRAFT, DISCARDED)."
    )

    confidence_score = models.FloatField(
        default=0.0,
        help_text="Agent-assigned confidence score for this keyword extraction."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Topic Keyword"
        verbose_name_plural = "Topic Keywords"
        indexes = [
            models.Index(fields=['workflow_state', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['workflow_state', 'text'],
                name='unique_keyword_per_session'
            )
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"[{self.status}] {self.text} for Session {self.workflow_state.session_id}"


class TopicScopeElement(models.Model):
    """
    Stores individual scope elements (Timeframe, Geography, Population, etc.) for the Initiation Phase.
    """

    SCOPE_STATUS_CHOICES = [
        ('LOCKED', 'Locked (Committed and Finalized)'),
        ('USER_DRAFT', 'User Draft (Created by User, Pending Review)'),
        ('AI_EXTRACTED', 'AI Extracted (Captured by Agent, Needs Review)'),
        ('ON_HOLD', 'On Hold (Excluded from Current Topic)'),
    ]

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        help_text="Unique identifier for the scope element entry."
    )

    workflow_state = models.ForeignKey(
        ResearchWorkflowState,
        on_delete=models.CASCADE,
        related_name='scope_elements_list',
        help_text="Foreign key linking the scope element to the parent research workflow session."
    )

    label = models.CharField(
        max_length=100,
        help_text="The category of the scope element (e.g., 'Timeframe', 'Geographical Focus')."
    )

    value = models.CharField(
        max_length=255,
        help_text="The specific defined value (e.g., '2020-2023', 'Southeast Asia')."
    )

    status = models.CharField(
        max_length=20,
        choices=SCOPE_STATUS_CHOICES,
        default='USER_DRAFT',
        help_text="The current status of the scope element (LOCKED, DRAFT, DISCARDED)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Topic Scope Element"
        verbose_name_plural = "Topic Scope Elements"
        indexes = [
            models.Index(fields=['workflow_state', 'label', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['workflow_state', 'label', 'value'],
                name='unique_scope_element_per_session'
            )
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"[{self.status}] {self.label}: {self.value} for Session {self.workflow_state.session_id}"
