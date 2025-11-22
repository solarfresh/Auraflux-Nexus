import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def get_user_group_name(user_id: int) -> str:
    """
    Generates the standardized Channel Group Name for a given user.
    This rule MUST be used by the consumer (to join) and the worker (to send).
    """
    return f'user_{user_id}'

def send_ws_notification(user_id: int, event_type: str, payload: dict):
    """
    Sends a generic notification to a specific user's WebSocket group.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logging.warning("Warning: Channel layer not configured. Cannot send WebSocket notification.")
        return

    user_group_name = get_user_group_name(user_id)

    async_to_sync(channel_layer.group_send)(
        user_group_name,
        {
            # 'type' must match the consumer method (e.g., send_notification -> send_notification)
            'type': 'send_notification',
            'event_type': event_type,
            'data': payload,
        }
    )