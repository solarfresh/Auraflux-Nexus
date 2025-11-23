import logging

from asgiref.sync import async_to_sync
from auraflux_core.core.clients.client_manager import ClientManager
from auraflux_core.core.schemas.clients import ClientConfig, ModelConfig
from django.apps import AppConfig
from django.conf import settings

from .utils import set_global_client_manager

logger = logging.getLogger(__name__)

class AgentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agents'
    label = 'agents'

    def ready(self):
        """
        Initializes the global ClientManager instance by loading configurations
        from settings.py.
        """
        self.initialize_client_manager()

    def initialize_client_manager(self):
        """
        Wraps the asynchronous initialization call using async_to_sync.
        """
        try:
            # Use async_to_sync for better integration with Django's thread safety
            async_to_sync(self._async_initialize_client_manager)()
        except Exception as e:
            # Catch all exceptions during startup initialization
            logger.error(f"Failed to initialize client manager asynchronously during startup: {e}")

    async def _async_initialize_client_manager(self):
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
                client_config = ClientConfig(models=core_model_configs)
                client_manager = ClientManager(client_config)
                await client_manager.initialize()
                set_global_client_manager(client_manager)
                logger.info("Global ClientManager initialized with %d models.", len(core_model_configs))
            except Exception as e:
                logger.critical(f"Failed to initialize global ClientManager: {e}")