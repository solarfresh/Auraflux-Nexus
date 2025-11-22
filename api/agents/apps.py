from django.apps import AppConfig


class AgentsConfig(AppConfig):
    """
    The responsibility is Agent Orchestration and Management.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agents'
    label = 'agents'
