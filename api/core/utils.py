from typing import Dict

from asgiref.sync import sync_to_async
from django.conf import settings


@sync_to_async
def get_serialized_data(query: Dict, model_class, serializer_class, many=True):
    instances = model_class.objects.filter(**query).all()
    serializer = serializer_class(instances, many=many)
    return serializer.data

def get_user_search_cache_key(user_id):
    """Generates a unique cache key for a user's search results."""
    return f"{settings.SEARCH_CACHE_KEY_PREFIX}:{user_id}"
