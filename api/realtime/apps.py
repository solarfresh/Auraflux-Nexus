# realtime/apps.py

from django.apps import AppConfig


class RealtimeConfig(AppConfig):
    """
    The responsibility is managing persistent connections (WebSockets/SSE)
    and acting as the transport layer for asynchronous notifications.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'realtime'
    label = 'realtime'