from auraflux_core.knowledge.schemas import GoogleSearchToolConfig
from auraflux_core.knowledge.tools import GoogleSearchTool
from django.apps import AppConfig
from django.conf import settings


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'
    label = 'search'

    google_search_tool: GoogleSearchTool | None = None

    def ready(self) -> None:
        self._initialize_google_search_tool()

    def _initialize_google_search_tool(self):
        config = GoogleSearchToolConfig(**settings.GOOGLE_SEARCH_CONFIG)
        self.google_search_tool = GoogleSearchTool(config=config)
