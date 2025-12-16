from core.constants import ResourceFormat, ResourceSource, WorkflowState
from core.models import BaseModel
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TopicKeyword(BaseModel):
    """
    Represents a semantic unit of the research topic.
    Corresponds to the 'TopicKeyword' interface in the frontend.
    """
    label = models.CharField(
        max_length=255,
        help_text="The text content of the keyword."
    )
    importance_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Weighted significance from 0.0 to 1.0."
    )
    is_core = models.BooleanField(
        default=False,
        help_text="Identifies if this is a central concept of the research."
    )
    semantic_category = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="e.g., 'Methodology', 'Theory', 'Technology'."
    )
    status = models.CharField(
        max_length=20,
        choices=WorkflowState.choices,
        default=WorkflowState.AI_EXTRACTED
    )

    def __str__(self):
        return f"{self.label} ({self.status})"


class TopicScopeElement(BaseModel):
    """
    Defines the boundaries of the research (Inclusions/Exclusions).
    Corresponds to the 'TopicScopeElement' interface.
    """
    class BoundaryType(models.TextChoices):
        INCLUSION = 'INCLUSION', 'Inclusion'
        EXCLUSION = 'EXCLUSION', 'Exclusion'

    label = models.CharField(
        max_length=255,
        help_text="The aspect of the scope (e.g., 'Timeframe', 'Geography')."
    )
    boundary_type = models.CharField(
        max_length=20,
        choices=BoundaryType.choices,
        default=BoundaryType.INCLUSION
    )
    rationale = models.TextField(
        help_text="The reasoning behind this boundary (originally 'value')."
    )
    status = models.CharField(
        max_length=20,
        choices=WorkflowState.choices,
        default=WorkflowState.AI_EXTRACTED
    )

    def __str__(self):
        return f"[{self.boundary_type}] {self.label}"


class ResourceItem(BaseModel):
    """
    A specific piece of information or document gathered during exploration.
    Acts as the source material for Reflection Entries.
    """
    label = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, null=True, blank=True)
    format = models.CharField(
        max_length=20,
        choices=ResourceFormat.choices,
        default=ResourceFormat.URL
    )
    source_type = models.CharField(
        max_length=20,
        choices=ResourceSource.choices,
        default=ResourceSource.MANUAL
    )
    summary = models.TextField(blank=True)
    raw_content = models.TextField(
        null=True,
        blank=True,
        help_text="Stored content for AI analysis or indexing."
    )

    # Relationships
    related_keywords = models.ManyToManyField(
        TopicKeyword,
        related_name='resources',
        blank=True
    )

    def __str__(self):
        return self.label