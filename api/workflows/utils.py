from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from users.models import User

from .models import (KnowledgeSource,  # Import all necessary models
                     WorkflowState)


@sync_to_async
def get_or_create_workflow_state(user: User) -> WorkflowState:
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
def update_workflow_state(user: User, **kwargs) -> WorkflowState:
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
            print(f"Warning: WorkflowState model has no field named '{field}'")

    # 3. Save the changes
    state.save()

    return state