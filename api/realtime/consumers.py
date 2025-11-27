import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from .utils import get_user_group_name

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Handles generic WebSocket connections for an authenticated user to receive
    real-time notifications from background tasks across all applications (e.g., workflows, agents).
    """

    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of connection.
        """
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            logger.warning("Anonymous user attempted to connect to NotificationConsumer.")
            await self.close()
            return

        self.user_id = user.id
        self.user_group_name = get_user_group_name(self.user_id)

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        logger.info("User %s connected to WebSocket. Channel added to group %s.",
                    self.user_id, self.user_group_name)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            logger.info("User %s disconnected from WebSocket.", self.user_id)

    # --- Communication Method (Generic Notification Handler) ---

    async def send_notification(self, event):
        """
        Receives a notification message from the worker via the Channels Layer
        and sends the data back to the client. This method is called when the
        worker uses {'type': 'send_notification'}.
        """
        event_type = event.get('event_type')
        payload = event.get('data', {})

        logger.debug("Received event '%s' for user %s. Sending to client.",
                     event_type, self.user_id)

        await self.send(text_data=json.dumps({
            'event_type': event_type,
            'status': event.get('status', 'success'),
            'payload': payload,
        }))

    async def receive(self, text_data=None, bytes_data=None):
        pass # Still keeping this empty for server-to-client transport
