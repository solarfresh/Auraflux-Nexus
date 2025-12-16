import uuid

from core.constants import ParticipantRole
from django.db import models


class BaseModel(models.Model):
    """
    An abstract base class that provides self-updating 'created_at'
    and 'updated_at' fields, using UUIDs for primary keys to ensure
    system-wide unique identification.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this entity."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The timestamp when this record was first created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The timestamp when this record was last modified."
    )

    class Meta:
        abstract = True


class SpatialMixin(models.Model):
    """
    A mixin for entities that exist within a 2D coordinate system,
    specifically for the Conceptual Map (Canvas) interactions.
    """
    x = models.FloatField(
        default=0.0,
        help_text="Horizontal coordinate on the canvas."
    )
    y = models.FloatField(
        default=0.0,
        help_text="Vertical coordinate on the canvas."
    )

    class Meta:
        abstract = True


class BaseCommunication(BaseModel):
    """
    An abstract model for chat messages and system logs.
    """
    role = models.CharField(
        max_length=20,
        choices=ParticipantRole.choices,
        default=ParticipantRole.USER,
        help_text="The role of the participant who sent the message."
    )
    content = models.TextField(help_text="The actual text content of the message.")
    sequence_number = models.PositiveIntegerField(
        help_text="Ordering index for the conversation flow."
    )

    class Meta:
        abstract = True
        ordering = ['sequence_number']