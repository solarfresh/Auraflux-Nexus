from django.db import models
from django.contrib.auth import get_user_model

# Use the default Django User model for association
User = get_user_model()


class WorkflowState(models.Model):
    """
    Stores the persistent state of a single strategic workflow canvas session.
    This model acts as the single source of truth for the entire analysis.
    """
    # Define available steps for clarity and validation
    STEP_CHOICES = [
        ('SEARCH', '1. Search & Data Lock'),
        ('SCOPE', '2. Define Scope & Tension'),
        ('COLLECTION', '3. Opinion Collection'),
        ('ANALYSIS', '4. Analyze Conflicts'),
        ('OUTPUT', '5. Final Strategy Output'),
    ]

    # Session Identifier: Using OneToOneField to link directly to the User
    # Assumes authenticated user sessions for persistence.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='workflow_state',
        verbose_name='Associated User'
    )

    # Current Step Status
    current_step = models.CharField(
        max_length=50,
        default='SEARCH',
        choices=STEP_CHOICES,
        help_text='The current active step in the workflow.'
    )

    # Search result fields
    query = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The search query that initially retrieved this result."
    )

    # Data from Step 2: Scope Definition
    scope_data = models.JSONField(
        default=None,
        help_text='Stores dichotomy, roles, and focused question.'
    )

    # Placeholder for future analysis results
    analysis_data = models.JSONField(
        default=None,
        help_text='Stores Agent opinions, conflict summaries, and final output data.'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State for {self.user.username} @ {self.current_step}"


class KnowledgeSource(models.Model):
    """
    Represents a single locked search result, serving as a source for RAG analysis.
    This model is linked to a specific WorkflowState.
    """
    # Foreign Key: Links this source to the parent workflow session
    workflow_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.CASCADE,
        related_name='knowledge_sources',
        help_text="The specific workflow session that has locked this source."
    )

    # Search result fields
    query = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The search query that initially retrieved this result."
    )
    title = models.CharField(max_length=255)
    snippet = models.TextField()
    url = models.URLField(max_length=500)
    source = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The source name (e.g., 'TechCrunch')."
    )

    # Tracking the time it was locked
    locked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Knowledge Sources"
        # Adding an index can improve performance when fetching all sources for a specific state
        indexes = [
            models.Index(fields=['workflow_state', 'url']),
        ]

    def __str__(self):
        return self.title[:50]