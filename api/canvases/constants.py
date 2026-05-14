from django.db import models
from django.utils.translation import gettext_lazy as _


class EdgeType(models.TextChoices):
    # --- Empirical Core ---
    VALIDATES = 'VALIDATES', _('Validates (Strong support)')
    CONSTRAINS = 'CONSTRAINS', _('Constrains (Restriction)')
    TRIGGERS = 'TRIGGERS', _('Triggers (Causal/Sequential)')

    # --- Functional ---
    REF = 'REF', _('Reference (Weak association)')
    LINK = 'LINK', _('Link (Structural connection)')


class NodeSolidity(models.TextChoices):
    SOLID = 'SOLID', _('Solid (Evidence-backed)')
    PULSING = 'PULSING', _('Pulsing (Hypothesis / Shadow)')
    DIMMED = 'DIMMED', _('Dimmed (Inbox / Placeholder)')


class NodeHandle(models.TextChoices):
    """
    """
    NORTH = 'n', _('North')
    EAST = 'e', _('East')
    WEST = 'w', _('West')
    SOUTH = 's', _('South')


class NodeType(models.TextChoices):
    # --- Empirical Core ---
    EVENT = 'EVENT', _('Event (Objective data points)')
    OUTCOME = 'OUTCOME', _('Outcome (Final results / North Star)')
    BOUNDARY = 'BOUNDARY', _('Boundary (Constraints / Scope)')
    ENTITY = 'ENTITY', _('Entity (Subjects / Tools)')

    # --- Canvas Functional ---
    FOCUS = 'FOCUS', _('Focus (Focal point of view)')
    RESOURCE = 'RESOURCE', _('Resource (External evidence items)')
    CONCEPT = 'CONCEPT', _('Concept (Logical bridges)')
    INSIGHT = 'INSIGHT', _('Insight (AI/Human Synthesis)')
    QUERY = 'QUERY', _('Query (Research gaps)')
    NAVIGATION = 'NAVIGATION', _('Navigation (Portal for View transitions)')
    GROUP = 'GROUP', _('Group (Container boundaries)')