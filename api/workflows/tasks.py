import json
import logging

from core.celery_app import celery_app
from realtime.utils import send_ws_notification

logger = logging.getLogger(__name__)

