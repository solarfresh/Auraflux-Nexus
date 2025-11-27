from django.urls import path

from .consumers import NotificationConsumer

urlpatterns = [
    path('ws/notifications/', NotificationConsumer.as_asgi(), name='ws-notification'),
]
