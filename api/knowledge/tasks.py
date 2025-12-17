import logging
from core.celery_app import celery_app
from messaging.constants import TopicKeywordsUpdated, TopicScopeElementsUpdated
from .models import TopicKeyword, TopicScopeElement


logger = logging.getLogger(__name__)


@celery_app.task(name=TopicKeywordsUpdated.name, ignore_result=True)
def update_topic_keywords(event_type: str, payload: dict):
    task_id = update_topic_keywords.request.id
    session_id = payload.get('session_id')
    refined_keywords = payload.get('refined_keywords_to_lock', [])
    for keyword_text in refined_keywords:
        TopicKeyword.objects.update_or_create(
            object_id=session_id,
            text=keyword_text,
            defaults={'status': 'AI_EXTRACTED'}
        )


@celery_app.task(name=TopicScopeElementsUpdated.name, ignore_result=True)
def update_topic_scope_elements(event_type: str, payload: dict):