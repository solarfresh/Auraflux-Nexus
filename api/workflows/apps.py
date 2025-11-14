from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    """
    The responsibility is responsibility is Workflow Management and State Persistence.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workflows'
    label = 'workflows'
