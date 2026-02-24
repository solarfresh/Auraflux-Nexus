import logging

from core.celery_app import celery_app
from messaging.constants import CreateNewCanvas
from canvases.utils import create_new_canvas_by_workflow_id

logger = logging.getLogger(__name__)

@celery_app.task(name=CreateNewCanvas.name, ignore_result=True)
def create_new_canvas(event_type: str, payload: dict):
    task_id = create_new_canvas.request.id
    workflow_id = payload.get('workflow_id')
    if workflow_id is None:
        logger.error('Task %s: workflow_id can not be None.', task_id)
        raise ValueError('workflow_id can not be None.')

    create_new_canvas_by_workflow_id(workflow_id)

    logger.info("Task %s: a new canvas was created for workflow %s.", task_id, workflow_id)
