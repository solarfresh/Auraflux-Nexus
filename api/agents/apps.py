import logging

from asgiref.sync import async_to_sync
from auraflux_core.core.clients.client_manager import ClientManager
from auraflux_core.core.schemas.clients import ClientConfig, ModelConfig
from celery.signals import worker_process_init
from django.apps import AppConfig
from django.conf import settings

from .utils import set_global_client_manager

logger = logging.getLogger(__name__)

class AgentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agents'
    label = 'agents'
    client_manager: ClientManager | None = None


async def _async_initialize_client_manager():
    """
    This method is called after the application is ready and migrations have run.
    It reads settings, converts them to Pydantic models, and initializes the ClientManager.
    """
    if not hasattr(settings, 'LLM_MODEL_CONFIGS'):
        logger.warning("settings.LLM_MODEL_CONFIGS is not defined. Agents functionality will be limited.")
        return

    core_model_configs = []

    # Iterate through settings and create CoreModelConfig instances
    for model_name, config_dict in settings.LLM_MODEL_CONFIGS.items():
        llm_config = ModelConfig(
            name=model_name,
            mode=config_dict['MODE'],
            base_url=config_dict.get('BASE_URL', None),
            api_key=config_dict.get('API_KEY'),
        )
        core_model_configs.append(llm_config)

    # Initialize and set global ClientManager
    if core_model_configs:
        try:
            client_config = ClientConfig(models=core_model_configs, initialize_mode='run_forever')
            client_manager = ClientManager(client_config)
            await client_manager.initialize()
            set_global_client_manager(client_manager)
            # AgentsConfig.client_manager = client_manager
            logger.info("Global ClientManager initialized with %d models.", len(core_model_configs))
        except Exception as e:
            logger.critical(f"Failed to initialize global ClientManager: {e}")


@worker_process_init.connect
def initialize_resources(sender=None, **kwargs):
    """Initializes resources for Celery worker processes."""
    async_to_sync(_async_initialize_client_manager)()
