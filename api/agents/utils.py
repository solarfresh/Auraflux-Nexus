import logging
from typing import Any, Optional
from auraflux_core.core.agents.generic_agent import GenericAgent
from auraflux_core.core.schemas.agents import AgentConfig

logger = logging.getLogger(__name__)

# Placeholder for the initialized ClientManager instance
_GLOBAL_CLIENT_MANAGER: Optional[Any] = None

def set_global_client_manager(client_manager: Any):
    """Sets the initialized ClientManager instance."""
    global _GLOBAL_CLIENT_MANAGER
    _GLOBAL_CLIENT_MANAGER = client_manager

def get_global_client_manager() -> Any:
    """Retrieves the initialized ClientManager instance."""
    if _GLOBAL_CLIENT_MANAGER is None:
        raise RuntimeError("ClientManager has not been initialized. Check agents/apps.py ready() method.")
    return _GLOBAL_CLIENT_MANAGER

def get_agent_instance(class_name: Any, agent_role_name: str) -> GenericAgent:
    try:
        role_config = class_name.objects.get(name=agent_role_name)
        client_manager = get_global_client_manager()
        if client_manager is None:
            raise RuntimeError("ClientManager is not initialized in AgentsConfig.")

        agent = GenericAgent(
            config=AgentConfig(
                name=role_config.name,
                system_message=role_config.system_prompt,
                model=role_config.llm_parameters.get('model_name', 'gemini-2.0-flash'),
            ),
            client_manager=client_manager
        )

        return agent
    except Exception as e:
        logger.critical("Failed to create agent instance for role %s: %s", agent_role_name, str(e))
        raise e
