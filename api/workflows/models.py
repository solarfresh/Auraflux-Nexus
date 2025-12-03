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


class InitiationPhaseData(models.Model):
    """
    Data Plane Model: Stores all phase-specific outputs, metrics,
    and control variables exclusive to the INITIATION stage (Kuhlthau 1).
    """

    # --- Linkage ---
    workflow_state = models.OneToOneField(
        ResearchWorkflowState,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='initiation_data',
        help_text="One-to-one link to the parent ResearchWorkflowState (Control Model)."
    )

    # --- INITIATION Phase Core Outputs & Metrics (Decisive Data) ---
    clarity_score = models.FloatField(
        default=0.0,
        help_text="The current Clarity Score (S) [0.0 - 1.0]. Used for decision making (L-4.1)."
    )
    da_activation_threshold = models.FloatField(
        default=0.35,
        help_text="The Clarity Score threshold (tau_DA) required to trigger the Data Agent's asynchronous work."
    )
    optimized_keywords = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Keywords (K') validated and optimized by the Data Agent (DA). Output of this phase."
    )

    # --- Cost Control & Agent Activation Variables (B-3.2) ---
    last_da_execution_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last completed Data Agent background validation run."
    )
    keyword_stability_count = models.IntegerField(
        default=0,
        help_text="Consecutive turns where preliminary keywords showed no significant change. Used for DA activation control."
    )

    # --- Transition Status (L-4.2) ---
    is_transition_ready = models.BooleanField(
        default=False,
        help_text="True if S > tau_EA AND K' has been updated. Used to enable the UI button."
    )

    # --- Detailed Agent Data & History (Verbose Storage) ---
    chat_history = JSONField(
        default=list,
        help_text="Stores the sequential conversation history for context passing."
    )
    unverified_keywords = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Keywords (K_pre) extracted by EA but not yet validated by DA."
    )
    da_validation_report = JSONField(
        default=dict,
        help_text="Detailed JSON report from the Data Agent (DA) after validation (includes IDF/QMS)."
    )
    ea_reasoning_log = JSONField(
        default=dict,
        help_text="Detailed reasoning log from the Explorer Agent (EA) for S calculation."
    )

    # --- Metadata ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Initiation Data for Session: {self.workflow_state.session_id}"

    class Meta:
        verbose_name = "Initiation Phase Data"
        verbose_name_plural = "Initiation Phase Data"
