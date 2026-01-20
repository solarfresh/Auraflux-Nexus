from types import SimpleNamespace
from uuid import UUID
from workflows.models import ExplorationPhaseData


def get_sidebar_registry_info(session_id: UUID, serializer_class=None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    exploration_instance = ExplorationPhaseData.objects.select_related(
        'workflow',
    ).get(
        workflow_id=session_id
    )

    sidebar_registry_info = SimpleNamespace(
        stability_score=exploration_instance.stability_score,
        final_research_question=exploration_instance.final_research_question,
        keywords=exploration_instance.workflow.keywords.all(),
        scope_elements=exploration_instance.workflow.scope_elements.all(),
    )

    serializer = serializer_class(sidebar_registry_info)
    return serializer.data
