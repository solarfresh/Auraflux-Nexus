import logging
from uuid import UUID

from core.constants import EntityStatus
from canvases.constants import NodeType
from canvases.models import (CanvasNodeRelation, ConceptualCanvas,
                             ConceptualNode)
from django.apps import apps

logger = logging.getLogger(__name__)


def create_new_canvas_by_workflow_id(workflow_id: UUID):
    ResearchWorkflow = apps.get_model('workflows', 'ResearchWorkflow')
    try:
        workflow = ResearchWorkflow.objects.get(workflow_id=workflow_id)
    except ResearchWorkflow.DoesNotExist:
        logger.error("Workflow with id %s does not exist. Cannot create canvas.", workflow_id)
        return

    canvas = ConceptualCanvas.objects.filter(workflow=workflow)

    if canvas.exists():
        logger.warning("Workflow %s already has a canvas. Skipping creation.", workflow_id)
        return

    canvas = ConceptualCanvas(name='Default Canvas', workflow=workflow)
    canvas.save()

    node = ConceptualNode(label=canvas.name, node_type='NAVIGATION')
    canvas.navigator.add(node, bulk=False)
    canvas.nodes.add(node, through_defaults={
        "status": EntityStatus.LOCKED}
    )

    return canvas
