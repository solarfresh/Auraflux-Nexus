from django.conf import settings


def get_user_cache_key(user_id):
    """Generates a unique cache key for a user's search results."""
    return f"{settings.SEARCH_CACHE_KEY_PREFIX}:{user_id}"