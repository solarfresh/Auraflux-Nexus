from django.urls import path

from .consumers import NotificationConsumer

urlpatterns = [
    path('ws/workflow/', NotificationConsumer.as_asgi(), name='ws-workflow-notification'),
]
