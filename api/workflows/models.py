import uuid

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import JSONField

# Use the default Django User model for association
User = get_user_model()


class KuhlthauStage(models.TextChoices):
    # [DB Value] = [Constant Name], [Human Readable Label]
    INITIATION = 'INITIATION', '1. Initiation (Uncertainty)'
    SELECTION = 'SELECTION', '2. Selection (Optimism)'
    EXPLORATION = 'EXPLORATION', '3. Exploration (Confusion/Doubt)'
    FORMULATION = 'FORMULATION', '4. Formulation (Clarity)'
    COLLECTION = 'COLLECTION', '5. Collection (Satisfaction)'
    PRESENTATION = 'PRESENTATION', '6. Presentation (Closure)'

    # 額外定義一個方便的屬性，例如用於狀態判斷
    @classmethod
    def get_emotional_state(cls, stage):
        if stage == cls.INITIATION:
            return 'Uncertainty'
        return 'N/A'


class ResearchWorkflowState(models.Model):
    """
    Core State Data Structure for managing a user's research workflow,
    tracking Kuhlthau phases, agent outputs, and cost control variables.
    """

    # Define choices for the Kuhlthau ISP stages
    KUHLTHAU_STAGES = (
        ('INITIATION', '1. Initiation (Uncertainty)'),
        ('SELECTION', '2. Selection (Optimism)'),
        ('EXPLORATION', '3. Exploration (Confusion/Doubt)'),
        ('FORMULATION', '4. Formulation (Clarity)'),
        ('COLLECTION', '5. Collection (Satisfaction)'),
        ('PRESENTATION', '6. Presentation (Closure)'),
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
        default=KuhlthauStage.INITIATION,
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


class UserReflectionLog(models.Model):
    """
    Stores individual user reflection entries for tracking emotional/cognitive state.
    """
    session_id = models.CharField(max_length=255, db_index=True)
    entry_text = models.TextField(help_text="The user's self-reported reflection text.")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reflection for {self.session_id} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


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

    latest_reflection_entry = models.ForeignKey(
        'UserReflectionLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyzed_in_initiation',
        help_text="The specific reflection log entry that was included in the last TR Agent structured analysis."
    )

    # --- Cost Control & Agent Activation Variables (Revising existing fields) ---
    # Renaming to reflect general Agent evaluation, not just DA
    # agent_evaluation_count = models.IntegerField(
    #     default=0,
    #     help_text="Consecutive turns where structured output showed no significant change. Used for control."
    # )
    # DA/Background Agent fields (keeping them for background validation logic)
    # da_activation_threshold = models.FloatField(
    #     default=4.0, # Adjusting threshold to fit 1-10 scale (e.g., score >= 4)
    #     help_text="The Stability Score threshold required to trigger the Data Agent's asynchronous work."
    # )
    # last_da_execution_time = models.DateTimeField(
    #     null=True,
    #     blank=True,
    #     help_text="Timestamp of the last completed Data Agent background validation run."
    # )

    # --- Detailed Agent Data & History (Logging) ---
    # agent_reasoning_log = JSONField(
    #     default=dict,
    #     blank=True,
    #     help_text="Detailed reasoning log from the Topic Refinement Agent (TR Agent) after structured output."
    # )
    # The existing DA report field can be repurposed or kept:
    # da_validation_report = JSONField(
    #     default=dict,
    #     help_text="Detailed JSON report from the Data Agent (DA) after validation (includes IDF/QMS)."
    # )

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

    initiation_data = models.ForeignKey(
        'InitiationPhaseData',
        on_delete=models.CASCADE,
        related_name='keywords_list',
        help_text="Link to the parent InitiationPhaseData record."
    )

    text = models.CharField(
        max_length=255,
        help_text="The keyword or key phrase itself."
    )

    status = models.CharField(
        max_length=20,
        choices=[('LOCKED', 'Locked'), ('DRAFT', 'Draft'), ('DISCARDED', 'Discarded')],
        default='DRAFT',
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
            models.Index(fields=['initiation_data', 'status']),
        ]

    def __str__(self):
        return f"[{self.status}] {self.text} for Session {self.initiation_data.workflow_state.session_id}"


class TopicScopeElement(models.Model):
    """
    Stores individual scope elements (Timeframe, Geography, Population, etc.) for the Initiation Phase.
    """
    initiation_data = models.ForeignKey(
        'InitiationPhaseData',
        on_delete=models.CASCADE,
        related_name='scope_elements_list',
        help_text="Link to the parent InitiationPhaseData record."
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
        choices=[('LOCKED', 'Locked'), ('DRAFT', 'Draft'), ('DISCARDED', 'Discarded')],
        default='DRAFT',
        help_text="The current status of the scope element (LOCKED, DRAFT, DISCARDED)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Topic Scope Element"
        verbose_name_plural = "Topic Scope Elements"
        indexes = [
            models.Index(fields=['initiation_data', 'label', 'status']),
        ]

    def __str__(self):
        return f"[{self.status}] {self.label}: {self.value} for Session {self.initiation_data.workflow_state.session_id}"
