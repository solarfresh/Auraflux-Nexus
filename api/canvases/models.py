from canvases.constants import EdgeType, NodeSolidity, NodeType
from core.constants import EntityStatus
from core.models import BaseModel, SpatialMixin
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ConceptualNode(BaseModel):
    label = models.CharField(max_length=500)
    node_type = models.CharField(
        max_length=20,
        choices=NodeType.choices,
        default=NodeType.CONCEPT
    )
    groundedness = models.IntegerField(
        default=5,
        help_text="Health Score (0-10). Values < 4 trigger visual alarm in frontend."
    )
    solidity = models.CharField(
        max_length=20,
        choices=NodeSolidity.choices,
        default=NodeSolidity.PULSING
    )

    # --- Knowledge Content (Empirical Layer) ---
    content = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed snippet or content description."
    )
    source_ref = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Grounding reference URL or document ID."
    )

    # --- AI Reasoning (Logic Layer) ---
    rationale = models.TextField(
        blank=True,
        null=True,
        help_text="AI's justification or reasoning for this node."
    )
    anchor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='descendants',
        help_text="Parent node for growth tracking/hierarchy."
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

    project = models.ForeignKey(
        'projects.ResearchProject',
        on_delete=models.CASCADE,
        related_name='project',
        help_text="Foreign key linking the message to the parent research project session."
    )

    class Meta:
        verbose_name = "Conceptual Node"
        verbose_name_plural = "Conceptual Nodes"


class ConceptualEdge(BaseModel):
    source = models.ForeignKey(
        'ConceptualNode',
        on_delete=models.CASCADE,
        related_name='outgoing_edges'
    )
    target = models.ForeignKey(
        'ConceptualNode',
        on_delete=models.CASCADE,
        related_name='incoming_edges'
    )
    source_handle = models.CharField(max_length=100, blank=True, null=True)
    target_handle = models.CharField(max_length=100, blank=True, null=True)

    # --- Metadata & Identification ---
    label = models.CharField(max_length=255, blank=True, null=True)
    edge_type = models.CharField(
        max_length=20,
        choices=EdgeType.choices,
        default=EdgeType.REF
    )

    # --- Knowledge & Grounding (Empirical Layer) ---
    evidence = models.TextField(
        blank=True,
        null=True,
        help_text="Logical justification for this link, crucial for Agentic Audit."
    )
    weight = models.FloatField(
        default=1.0,
        help_text="Strength of the relationship."
    )

    # --- AI Reasoning & Metadata (Logic Layer) ---
    rationale = models.TextField(
        blank=True,
        null=True,
        help_text="AI's reasoning behind establishing this connection."
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Scenario-specific data like timestamps, confidence scores, etc."
    )

    canvas = models.ForeignKey(
        'ConceptualCanvas',
        on_delete=models.CASCADE,
        related_name='edge',
        help_text="Foreign key linking the edge to its parent canvas."
    )

    class Meta:
        verbose_name = "Conceptual Edge"
        verbose_name_plural = "Conceptual Edges"
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'target', 'canvas'],
                name='unique_conceptual_edge_per_canvas'
            )
        ]

    def __str__(self):
        return f"{self.source.label} --[{self.edge_type}]--> {self.target.label}"


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
    project = models.ForeignKey(
        'projects.ResearchProject',
        on_delete=models.CASCADE,
        help_text="The ID of the user owning this project."
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
    status = models.CharField(
        max_length=20,
        choices=EntityStatus.choices,
        default=EntityStatus.AI_EXTRACTED
    )
    rationale = models.CharField(help_text="The logic or reasoning behind the node's placement or selection.")

    class Meta:
        verbose_name = "Canvas Node Relation"
        verbose_name_plural = "Canvas Node Relations"
        constraints = [
            models.UniqueConstraint(
                fields=['node', 'canvas'],
                name='unique_conceptual_node_per_canvas'
            )
        ]
