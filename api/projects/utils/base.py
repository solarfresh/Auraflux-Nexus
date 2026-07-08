from typing import TYPE_CHECKING
from uuid import UUID

from django.contrib.auth import get_user_model

from projects.models import ResearchProject


if TYPE_CHECKING:
    from users.models import User
else:
    User = get_user_model()

def create_project(project_id: UUID, user_id: UUID, initial_stage: str) -> ResearchProject:
    """
    Creates a new ResearchEntityStatus instance.
    """
    return ResearchProject.objects.create(
        id=project_id,
        user_id=user_id,
        current_stage=initial_stage
    )

def get_project_by_id(project_id: UUID, user_id: UUID) -> ResearchProject:
    """
    Retrieves an existing ResearchEntityStatus instance.
    If not found, it raises a DoesNotExist exception (for 404 handling in the View).
    """
    # Note: Use get_object_or_404 in the View or handle the DoesNotExist here.
    return ResearchProject.objects.get(
        id=project_id,
        user_id=user_id
    )
