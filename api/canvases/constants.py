from django.db import models
from django.utils.translation import gettext_lazy as _


class NodeSolidity(models.TextChoices):
    """
    """
    SOLID = 'SOLID', _('Solid')
    PULSING = 'PULSING', _('Pulsing')
    DIMMED = 'DIMMED', _('Dimmed')


class NodeType(models.TextChoices):
    """
    """
    FOCUS = 'FOCUS', _('Focus')
    RESOURCE = 'RESOURCE', _('Resource')
    CONCEPT = 'CONCEPT', _('Concept')
    INSIGHT = 'INSIGHT', _('Insight')
    QUERY = 'QUERY', _('Query')
    GROUP = 'GROUP', _('Group')
    NAVIGATION = 'NAVIGATION', _('Navigation')
