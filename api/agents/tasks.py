import json
import logging
from typing import Any, Dict

from agents.agents.generic_agent import \
    GenericAgent  # The concrete agent class
from auraflux_core.core.schemas.agents import AgentConfig
from core.celery_app import celery_app
from messaging.constants import DICHOTOMY_SUGGESTION_COMPLETED
from messaging.tasks import publish_event

from .models import AgentRoleConfig
from .utils import get_global_client_manager

logger = logging.getLogger(__name__)

@celery_app.task(name='handle_suggestion_request_event', ignore_result=True)
def handle_suggestion_request_event(event_type: str, payload: dict):
    """
    Consumer task for the DICHOTOMY_SUGGESTION_REQUESTED event.

    1. Loads the agent configuration (coupling to AgentRoleConfig).
    2. Runs the AI computation.
    3. Publishes the DICHOTOMY_SUGGESTION_COMPLETED event (decoupled response).
    """

    workflow_state_id = payload.get('workflow_state_id')
    user_id = payload.get('user_id')
    input_data = payload.get('input_data')
    agent_role_name = payload.get('agent_role_name')

    if not all([workflow_state_id, user_id, input_data, agent_role_name]):
        logger.error("Missing required fields in event payload for task ID: %s", celery_app.request.id)
        return

    logger.info("Agent starting computation for WF ID %s (Role: %s)", workflow_state_id, agent_role_name)

    try:
        # Load Configuration (Coupling to the AGENTS app's local model)
        role_config = AgentRoleConfig.objects.get(name=agent_role_name)
        client_manager = get_global_client_manager()
        agent = GenericAgent(
            config=AgentConfig(**agent_config_data),
            client_manager=client_manager
        )

        # Run Agent Computation
        suggestions_json_str: str = agent.generate_suggestions_from_text(
            text=input_data,
            system_prompt=role_config.system_prompt,
            output_schema=role_config.output_schema
        )

        suggestions_data: Dict[str, Any] = json.loads(suggestions_json_str)
        logger.info("Agent computation complete. Generated %d suggestions.", len(suggestions_data))

        # 3. Publish Completion Event to the Bus
        # The WORKFLOWS app listener will pick this up to update the cache and notify the user.
        completion_payload = {
            "workflow_state_id": workflow_state_id,
            "user_id": user_id,
            "suggestions": suggestions_data # Pass the final computed data
        }

        publish_event.delay(
            event_type=DICHOTOMY_SUGGESTION_COMPLETED,
            payload=completion_payload
        )
        logger.info("Published %s event for WF ID %s.", DICHOTOMY_SUGGESTION_COMPLETED, workflow_state_id)

    except AgentRoleConfig.DoesNotExist:
        logger.error("Agent role config '%s' not found. Cannot compute suggestions.", agent_role_name)
    except Exception as e:
        logger.critical("AI Agent computation failed for WF ID %s: %s", workflow_state_id, str(e))
        # Re-raise to ensure Celery records the task as failed
        raise