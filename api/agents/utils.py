import json
import logging
from typing import Any, Dict, Optional, Tuple

from auraflux_core.core.agents.generic_agent import GenericAgent
from auraflux_core.core.schemas.agents import AgentConfig
from auraflux_core.core.schemas.messages import Message

logger = logging.getLogger(__name__)

# Placeholder for the initialized ClientManager instance
_GLOBAL_CLIENT_MANAGER: Optional[Any] = None

def compose_prompt(
    rendered_data: Dict[str, Any],
    prompt_template: str,
    template_variables: Dict[str, Any]
) -> Optional[str]:
    """
    Composes the final LLM prompt string by filling the prompt template with rendered data.

    Args:

    Returns:
        The fully composed prompt string, or None if the template is missing.
    """

    required_variables = set(template_variables.keys())
    missing_variables = required_variables - set(rendered_data.keys())

    if missing_variables:
        logger.error(
            f"Prompt rendering aborted. Missing required data for variables: {missing_variables}"
        )
        # For production robustness, we might substitute missing variables with a fallback (e.g., 'N/A')
        # or raise a specific error. Here, we return None.
        return None

    try:
        # We need to wrap variable names with curly braces to match the {{var}} syntax
        # often used in templates and then replace them using the dictionary keys.

        # A simple replacement loop is robust against special characters, unlike using .format directly
        # on the entire text which requires careful handling of all existing braces {}.

        composed_prompt = prompt_template
        for key, value in rendered_data.items():
            # Ensure the value is converted to string for safe insertion
            str_value = str(value) if value is not None else ""

            # Replace the {{key}} placeholder with the actual value
            composed_prompt = composed_prompt.replace("{{" + key + "}}", str_value)

        return composed_prompt.strip()

    except Exception as e:
        logger.critical(f"Error during prompt template rendering: {e}")
        return None

async def get_agent_response(agent_config_class, agent_role_name, prompt_text=None, rendered_data=None, output_format: str = 'text') -> Any:
    """
    Retrieves the agent response based on either a direct prompt text or rendered data.

    Args:
        agent_config_class: The class representing the agent configuration.
        agent_role_name: The role name of the agent.
        prompt_text: Direct prompt text to send to the agent.
        rendered_data: Data to be used for composing the prompt.
        output_format: Desired output format ('text' or 'json').
    """

    if prompt_text is None and rendered_data is None:
        raise ValueError("Either prompt_text or rendered_data must be provided.")

    agent, role_config = get_agent_instance(agent_config_class, agent_role_name)

    if prompt_text is not None:
        prompt = prompt_text
    elif rendered_data is not None:
        prompt = compose_prompt(rendered_data, role_config.prompt_template, role_config.template_variables)
    else:
        raise ValueError("Unable to compose prompt: insufficient data provided.")

    try:
        message = await agent.generate(
            messages=[Message(role="user", content=prompt, name='User')]
        )

        if output_format == 'json':
            return json.loads(message.content.replace('```json', '').replace('```', '').strip())
        elif output_format == 'text':
            return message.content
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    except Exception as e:
        raise e

def get_handle_topic_refinement_agent_request_key(session_id: str) -> str:
    return f"handle_topic_refinement_agent_request:{session_id}"

def set_global_client_manager(client_manager: Any):
    """Sets the initialized ClientManager instance."""
    global _GLOBAL_CLIENT_MANAGER
    _GLOBAL_CLIENT_MANAGER = client_manager

def get_global_client_manager() -> Any:
    """Retrieves the initialized ClientManager instance."""
    if _GLOBAL_CLIENT_MANAGER is None:
        raise RuntimeError("ClientManager has not been initialized. Check agents/apps.py ready() method.")
    return _GLOBAL_CLIENT_MANAGER

def get_agent_instance(class_name: Any, agent_role_name: str) -> Tuple[GenericAgent, Any]:
    try:
        role_config = class_name.objects.get(name=agent_role_name)
        client_manager = get_global_client_manager()
        if client_manager is None:
            raise RuntimeError("ClientManager is not initialized in AgentsConfig.")

        agent_config = {
            "name": role_config.name,
            "system_message": role_config.system_prompt,
            **role_config.llm_parameters
        }

        agent = GenericAgent(
            config=AgentConfig(**agent_config),
            client_manager=client_manager
        )

        return agent, role_config
    except Exception as e:
        logger.critical("Failed to create agent instance for role %s: %s", agent_role_name, str(e))
        raise e
