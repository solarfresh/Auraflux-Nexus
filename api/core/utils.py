from typing import Any, Dict
from uuid import UUID

from django.conf import settings


def get_serialized_data(query: Dict, model_class, serializer_class, many=True):
    instances = model_class.objects.filter(**query).all()
    serializer = serializer_class(instances, many=many)
    return serializer.data

def get_serialized_data_by_id(id: UUID, model_class, serializer_class):
    instance = model_class.objects.get(id=id)
    serializer = serializer_class(instance)
    return serializer.data

def get_user_search_cache_key(user_id):
    """Generates a unique cache key for a user's search results."""
    return f"{settings.SEARCH_CACHE_KEY_PREFIX}:{user_id}"

def update_serialized_data_by_id(id: UUID, data: Dict[str, Any], model_class, serializer_class):
    instance = model_class.objects.get(id=id)
    serializer = serializer_class(
        instance=instance,
        data=data,
        partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return serializer.data
    else:
        raise serializer.errors

