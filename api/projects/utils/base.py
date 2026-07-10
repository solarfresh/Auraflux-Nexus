import logging
from typing import TYPE_CHECKING, Any, Dict, cast
from uuid import UUID

from django.contrib.auth import get_user_model
from projects.models import ResearchProject
from projects.serializers import ProjectSerialize
from projects.utils.consultation import get_or_create_consultation_data
from projects.utils.exploration import get_or_create_exploration_data

if TYPE_CHECKING:
    from users.models import User
else:
    User = get_user_model()

logger = logging.getLogger(__name__)

def create_project(data: Dict[str, Any], user_id: str):
    """
    Creates a new ResearchEntityStatus instance.
    """


    serializer = ProjectSerialize(data=data)
    if serializer.is_valid():
        instance = serializer.save(user_id=user_id)
        project = cast(ResearchProject, instance)

        get_or_create_consultation_data(
            project=project,
        )
        get_or_create_exploration_data(
            project=project,
        )

        return serializer.data
    else:
        return serializer.errors


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
