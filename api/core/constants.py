from django.db import models
from django.utils.translation import gettext_lazy as _


class FeasibilityStatus(models.TextChoices):
    """
    Feasibility assessment for research topics (U.S. 1).
    Used to track the viability of a research question.
    """
    HIGH = 'HIGH', _('High')
    MEDIUM = 'MEDIUM', _('Medium')
    LOW = 'LOW', _('Low')


class ParticipantRole(models.TextChoices):
    """
    Standardized roles for communication and logging.
    Ensures consistency between AI agent interactions and user messages.
    """
    USER = 'user', _('User')
    SYSTEM = 'system', _('System')
    AI_AGENT = 'ai-agent', _('AI Agent')


class EntityStatus(models.TextChoices):
    """
    Workflow state tokens used for consistent styling and
    logic across different node types and UI components.
    """
    USER_DRAFT = 'USER_DRAFT', _('User Draft')
    AI_EXTRACTED = 'AI_EXTRACTED', _('AI Extracted')
    LOCKED = 'LOCKED', _('Locked')
    ON_HOLD = 'ON_HOLD', _('On Hold')
    ARCHIVED = 'ARCHIVED', _('Archived')


class ISPStep(models.TextChoices):
    """
    Information Search Process (ISP) Phases.
    Maps to the global workflow progress tracking.
    """
    DEFINITION = 'DEFINITION', _('Definition')
    EXPLORATION = 'EXPLORATION', _('Exploration')
    FORMULATION = 'FORMULATION', _('Formulation')
    COLLECTION = 'COLLECTION', _('Collection')
    PRESENTATION = 'PRESENTATION', _('Presentation')


class ResourceFormat(models.TextChoices):
    """Supported formats for research materials."""
    URL = 'URL', _('Web URL')
    PDF = 'PDF', _('PDF Document')
    DOCUMENT = 'DOCUMENT', _('Local Document')
    IMAGE = 'IMAGE', _('Visual Data')
    SNIPPET = 'SNIPPET', _('Text Snippet')


class ResourceSource(models.TextChoices):
    """Primary sources for gathered research items."""
    ACADEMIC = 'ACADEMIC', _('Academic Source')
    NEWS = 'NEWS', _('News/Media')
    SOCIAL = 'SOCIAL', _('Social Discourse')
    GOVERNMENT = 'GOVERNMENT', _('Official/Policy')
    MANUAL = 'MANUAL', _('Manual Input')
    AI_GENERATED = 'AI_GENERATED', _('AI Synthesized')