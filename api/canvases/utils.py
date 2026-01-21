from uuid import UUID
from canvases.constants import NodeType
from canvases.models import ConceptualCanvas, ConceptualNode, CanvasNodeRelation


def create_new_canvas_by_workflow_id(workflow_id: UUID):
    canvas = ConceptualCanvas(name='Default Canvas', workflow_id=workflow_id)
    canvas.save()

    node = ConceptualNode(label=canvas.name, node_type='NAVIGATION')
    canvas.navigator.add(node, bulk=False)
    canvas.nodes.add(node)

    return canvas
