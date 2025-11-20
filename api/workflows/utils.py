import logging
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction

from .models import KnowledgeSource, WorkflowState

if TYPE_CHECKING:
    from users.models import User
else:
    User = get_user_model()


@sync_to_async
def get_and_persist_cached_results(user: "User", cache_key: str) -> bool:
    """
    Retrieves transient search data from the cache, saves it to the database,
    atomically updates the WorkflowState to 'SCOPE', and clears the cache.

    Args:
        user: The authenticated Django User instance.
        cache_key: The unique key used to retrieve the data from the cache.

    Returns:
        True if data was found, persisted, and the step updated; False otherwise.
    """
    # Retrieve Data from Cache
    cached_data = cache.get(cache_key)

    if not cached_data or not cached_data.get('results'):
        # If cache is empty or results are missing, return False (signals HTTP 400 to view)
        return False

    search_query = cached_data.get('query', 'N/A')
    search_results = cached_data.get('results', [])

    try:
        with transaction.atomic():
            # 2. Retrieve the WorkflowState (must exist due to prior checks in the view)
            state = WorkflowState.objects.get(user=user)

            # --- Persistence Actions ---

            # 3. Update WorkflowState with the final query and transition step
            state.current_step = 'SCOPE'
            state.save()

            # 4. Clean up any previous knowledge sources associated with this state
            # This is crucial if a user re-locks data after stepping back or changing their mind.
            KnowledgeSource.objects.filter(workflow_state=state).delete()

            # 5. Prepare and Bulk Create KnowledgeSource records
            sources_to_create = [
                KnowledgeSource(
                    workflow_state=state,
                    query=search_query,
                    title=result.get('title', ''),
                    snippet=result.get('snippet', ''),
                    url=result.get('url', ''),
                    source=result.get('source', ''),
                    # locked_at will be set automatically by auto_now_add
                ) for result in search_results
            ]

            if sources_to_create:
                KnowledgeSource.objects.bulk_create(sources_to_create)

        # 6. Cleanup cache (only if the atomic transaction was successful)
        cache.delete(cache_key)

        return True

    except WorkflowState.DoesNotExist:
        # This error should be rare due to prior 'get_or_create' in the view,
        # but handled here for safety.
        return False
    except Exception as e:
        # The transaction block automatically handles rollback upon any exception.
        logging.error(f"Error persisting cached data for user {user.pk}: {e}")
        # Re-raise the exception to allow the calling view to handle the HTTP 500 response.
        raise e

@sync_to_async
def get_or_create_workflow_state(user: "User") -> WorkflowState:
    """
    Retrieves the existing WorkflowState for a user or creates a new one
    if it does not exist.
    """
    # Note: Using get_or_create is safer than separate try/except blocks
    state, created = WorkflowState.objects.get_or_create(
        user=user,
        defaults={
            # Set initial defaults if a new state is created
            'current_step': 'SEARCH',
            'scope_data': {},
            'analysis_data': {},
        }
    )
    return state

@sync_to_async
def update_workflow_state(user: "User", **kwargs) -> WorkflowState:
    """
    Updates specific fields of the user's existing WorkflowState.
    Requires the state to already exist.

    Args:
        user: The Django User instance.
        **kwargs: Fields to update (e.g., current_step='SCOPE', scope_data={...}).

    Raises:
        WorkflowState.DoesNotExist: If the state record is missing.
    """
    # 1. Retrieve the state (or use get_or_create if you want to handle missing states)
    try:
        state = WorkflowState.objects.get(user=user)
    except WorkflowState.DoesNotExist:
        # For updates, we usually want to raise an error if the state is missing.
        raise

    # 2. Update all provided fields
    for field, value in kwargs.items():
        if hasattr(state, field):
            setattr(state, field, value)
        else:
            # Optional: Log a warning if an invalid field is passed
            logging.warning(f"Warning: WorkflowState model has no field named '{field}'")

    # 3. Save the changes
    state.save()

    return state