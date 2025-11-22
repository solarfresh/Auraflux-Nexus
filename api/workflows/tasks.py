import importlib
import logging

from core.celery_app import celery_app
from django.conf import settings

logger = logging.getLogger(__name__)

@celery_app.task(name='dispatch_agent_task')
def dispatch_agent_task(agent_role_name: str, workflow_state_id: int, input_data: str):
    """
    A generic dispatcher task executed by the worker fleet.
    It dynamically loads and executes the specific agent handler based on the role name
    defined in the centralized AGENT_HANDLER_MAP setting.
    """

    # Retrieve the AGENT_HANDLER_MAP from settings
    # This setting must be defined in settings.py and map role names to
    # the FULL PYTHON PATH of the handler function (e.g., 'agents.tasks.handle_dichotomy_suggestion').
    handler_map = getattr(settings, 'AGENT_HANDLER_MAP', {})

    # Lookup the full Python path for the handler function
    handler_path = handler_map.get(agent_role_name)

    if not handler_path:
        logger.error("Unknown agent role or missing handler path in settings: %s", agent_role_name)
        # In a real system, you might raise an exception here to trigger a dead-letter queue
        # or notify an administrator. For now, we return.
        return

    try:
        # Dynamically load the function (the coupling happens here via path, not import)
        # Split the path into module and function name
        module_path, func_name = handler_path.rsplit('.', 1)

        # Import the module (e.g., agents.tasks)
        module = importlib.import_module(module_path)

        # Get the function object (e.g., handle_dichotomy_suggestion)
        handler_func = getattr(module, func_name)

    except (ImportError, AttributeError) as e:
        logger.error("Failed to dynamically load agent handler function '%s': %s", handler_path, str(e))
        return

    # Execute the specific agent logic
    logger.info("Dispatching task for role '%s' to handler: %s", agent_role_name, handler_path)
    try:
        handler_func(
            workflow_state_id=workflow_state_id,
            input_data=input_data
        )
    except Exception as e:
        logger.error("Execution failed for agent role '%s': %s", agent_role_name, str(e))
        # Depending on complexity, you might re-raise the exception or handle failure states here.