from canvases.constants import NodeSolidity, NodeType
from core.models import BaseModel, SpatialMixin
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ConceptualNode(BaseModel):
    label = models.CharField(max_length=500)
    node_type = models.CharField(
        max_length=20,
        choices=NodeType.choices
    )
    groundedness = models.IntegerField(
        default=5,
        help_text=""
    )
    solidity = models.CharField(
        max_length=20,
        choices=NodeSolidity.choices,
        default=NodeSolidity.PULSING
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text=""
    )
    object_id = models.UUIDField(
        help_text="The UUID of the specific owner instance."
    )
    owner = GenericForeignKey('content_type', 'object_id')
    canvases = models.ManyToManyField(
        'ConceptualCanvas',
        related_name='node',
        through='CanvasNodeRelation',
    )

    class Meta:
        verbose_name = "Conceptual Node"
        verbose_name_plural = "Conceptual Nodes"


class ConceptualCanvas(BaseModel):
    name = models.CharField(max_length=24)
    nodes = models.ManyToManyField(
        'ConceptualNode',
        related_name='canvas',
        through='CanvasNodeRelation',
    )
    navigator = GenericRelation(
        "ConceptualNode",
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='owner'
    )
    workflow = models.ForeignKey(
        'workflows.ResearchWorkflow',
        on_delete=models.CASCADE,
        help_text="The ID of the user owning this workflow."
    )

    class Meta:
        verbose_name = "Conceptual Canvas"
        verbose_name_plural = "Conceptual Canvases"


class CanvasNodeRelation(BaseModel, SpatialMixin):
    node = models.ForeignKey(
        'ConceptualNode',
        on_delete=models.CASCADE
    )
    canvas = models.ForeignKey(
        'ConceptualCanvas',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Canvas Node Relation"
        verbose_name_plural = "Canvas Node Relations"
