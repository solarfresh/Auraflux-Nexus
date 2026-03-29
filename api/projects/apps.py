from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """
    The responsibility is responsibility is Project Management and State Persistence.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'
    label = 'projects'
