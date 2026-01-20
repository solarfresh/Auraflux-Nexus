from typing import TYPE_CHECKING
from uuid import UUID

from django.contrib.auth import get_user_model

from ..models import ReflectionLog, ResearchWorkflow

if TYPE_CHECKING:
    from users.models import User
else:
    User = get_user_model()

def create_workflow(session_id: UUID, user_id: int, initial_stage: str) -> ResearchWorkflow:
    """
    Creates a new ResearchEntityStatus instance.
    """
    return ResearchWorkflow.objects.create(
        session_id=session_id,
        user_id=user_id,
        current_stage=initial_stage
    )

def get_resource_suggestion(feasibility_status: str) -> str:
    if feasibility_status == 'HIGH':
        return "Focus your next search using specialized academic databases (e.g., Scopus, Web of Science) targeting the specific geographical and time scope."
    elif feasibility_status == 'MEDIUM':
        return "Use a combination of general search engines and credible institutional reports (e.g., OECD, World Bank) to solidify your topic."
    elif feasibility_status == 'LOW':
        return "The topic is highly niche or information-scarce. Start with broad keyword searches and general encyclopedias to establish foundational context before narrowing down."
    return "Please define your topic further to get a resource suggestion."

def create_reflection_log_by_session(session_id: UUID, reflection_log_title: str, reflection_log_content: str, reflection_log_status: str | None = None, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    try:
        workflow = ResearchWorkflow.objects.get(session_id=session_id)
    except ResearchWorkflow.DoesNotExist:
        return

    ReflectionLog = workflow.reflection_logs.model
    new_log = ReflectionLog(
        title=reflection_log_title,
        content=reflection_log_content,
        status='DRAFT'
    )

    if reflection_log_status is not None:
        new_log.status = reflection_log_status

    workflow.reflection_logs.add(new_log, bulk=False)
    instances = workflow.reflection_logs.all()
    serializer = serializer_class(instances, many=True)
    return serializer.data

def update_reflection_log_by_id(log_id: UUID, reflection_log_title: str, reflection_log_content: str, reflection_log_status: str | None = None, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    log_instance = ReflectionLog.objects.get(id=log_id)

    log_instance.title = reflection_log_title
    log_instance.content = reflection_log_content
    if reflection_log_status is not None:
        log_instance.status = reflection_log_status

    log_instance.save()

    instances = ReflectionLog.objects.filter(object_id=log_instance.object_id).all()
    serializer = serializer_class(instances, many=True)
    return serializer.data

def get_reflection_log_by_session(session_id: UUID, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    try:
        workflow = ResearchWorkflow.objects.get(session_id=session_id)
    except ResearchWorkflow.DoesNotExist:
        return

    instances = workflow.reflection_logs.all()
    serializer = serializer_class(instances, many=True)
    return serializer.data

def create_topic_scope_element_by_session(session_id: UUID, scope_label: str, scope_rationale: str, scope_status: str | None = None, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    try:
        workflow = ResearchWorkflow.objects.get(session_id=session_id)
    except ResearchWorkflow.DoesNotExist:
        return

    TopicScopeElement = workflow.scope_elements.model
    new_scope = TopicScopeElement(
        label=scope_label,
        rationale=scope_rationale,
        status='USER_DRAFT'
    )

    if scope_status is not None:
        new_scope.status = scope_status

    new_scope.save()

    instances = workflow.scope_elements.all()
    serializer = serializer_class(instances, many=True)
    return serializer.data

def get_topic_scope_element_by_session(session_id: UUID, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    try:
        workflow = ResearchWorkflow.objects.get(session_id=session_id)
    except ResearchWorkflow.DoesNotExist:
        return

    instances = workflow.scope_elements.all()
    serializer = serializer_class(instances, many=True)
    return serializer.data

def create_topic_keyword_by_session(session_id: UUID, keyword_label: str, keyword_status: str | None = None, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    try:
        workflow = ResearchWorkflow.objects.get(session_id=session_id)
    except ResearchWorkflow.DoesNotExist:
        return

    TopicKeyword = workflow.keywords.model
    new_keyword = TopicKeyword(
        label=keyword_label,
        status='USER_DRAFT'
    )
    if keyword_status is not None:
        new_keyword.status = keyword_status

    workflow.keywords.add(new_keyword, bulk=False)

    instances = workflow.keywords.all()
    serializer = serializer_class(instances, many=True)
    return serializer.data

def get_topic_keyword_by_session(session_id: UUID, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    try:
        workflow = ResearchWorkflow.objects.get(session_id=session_id)
    except ResearchWorkflow.DoesNotExist:
        return

    instances = workflow.keywords.all()
    serializer = serializer_class(instances, many=True)
    return serializer.data

def get_workflow(session_id: UUID, user_id: int) -> ResearchWorkflow:
    """
    Retrieves an existing ResearchEntityStatus instance.
    If not found, it raises a DoesNotExist exception (for 404 handling in the View).
    """
    # Note: Use get_object_or_404 in the View or handle the DoesNotExist here.
    return ResearchWorkflow.objects.get(
        session_id=session_id,
        user_id=user_id
    )
