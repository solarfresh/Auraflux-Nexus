from types import SimpleNamespace
from typing import TYPE_CHECKING, Dict
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import InitiationPhaseData, ReflectionLog, ResearchWorkflow

if TYPE_CHECKING:
    from users.models import User
else:
    User = get_user_model()

def atomic_read_and_lock_initiation_data(session_id: UUID, user_id: int) -> tuple[ResearchWorkflow, InitiationPhaseData]:
    """
    Executes a single atomic transaction to lock the state and load the initiation data.
    This is the function called by the WorkflowChatInputView.
    """

    # Ensures the entire sequence is locked and atomic
    with transaction.atomic():
        # Retrieve and LOCK the main state
        # Note: Must use select_for_update() for locking
        workflow = get_object_or_404(
            ResearchWorkflow.objects.select_for_update(),
            session_id=session_id,
            user_id=user_id
        )

        # Retrieve or Create and LOCK the phase data
        # We need to get or create the InitiationPhaseData instance.
        # Since it is a OneToOne relationship, the lock on the parent often suffices,
        # but select_for_update() is safer if the instance exists.

        # We call the synchronous helper function *within* the atomic block
        initiation_data = get_or_create_initiation_data(workflow)

        # Manually lock the data instance if necessary (complex locking is usually done via raw query or dedicated manager)
        # initiation_data = InitiationPhaseData.objects.select_for_update().get(workflow=workflow)

        return workflow, initiation_data

def patch_initiation_phase_data(session_id: UUID, data: Dict, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    instance = InitiationPhaseData.objects.get(workflow__session_id=session_id)
    serializer = serializer_class(instance, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()

    raise serializer.errors

def get_refined_topic_instance(session_id: UUID, serializer_class=None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    initiation_instance = InitiationPhaseData.objects.select_related(
        'workflow',
    ).get(
        workflow_id=session_id
    )

    refined_topic = SimpleNamespace(
            stability_score=initiation_instance.stability_score,
            feasibility_status=initiation_instance.feasibility_status,
            final_research_question=initiation_instance.final_research_question,
            keywords=initiation_instance.workflow.keywords.all(),
            scope_elements=initiation_instance.workflow.scope_elements.all(),
            resource_suggestion= get_resource_suggestion(initiation_instance.feasibility_status)
    )

    serializer = serializer_class(refined_topic)
    return serializer.data

def create_workflow(session_id: UUID, user_id: int, initial_stage: str) -> ResearchWorkflow:
    """
    Creates a new ResearchEntityStatus instance.
    """
    return ResearchWorkflow.objects.create(
        session_id=session_id,
        user_id=user_id,
        current_stage=initial_stage
    )

def determine_feasibility_status(score: int, is_niche: bool) -> str:
    """Helper function to determine the final Feasibility Status based on Agent output and rules."""
    if is_niche or score < 4:
        return 'LOW'
    if score >= 8:
        return 'HIGH'
    return 'MEDIUM'

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

def get_or_create_initiation_data(workflow: ResearchWorkflow) -> InitiationPhaseData:
    """
    Retrieves or creates the InitiationPhaseData linked to the workflow state.
    Handles phase-specific default value initialization.

    NOTE: Don't be decorate this function with @sync_to_async.
    This function is used by atomic_read_and_lock_initiation_data and is
    intended to be called within an atomic transaction.
    """
    # Using get_or_create to safely handle the OneToOne relationship
    initiation_data, created = InitiationPhaseData.objects.get_or_create(
        workflow=workflow,
        defaults={
            'stability_score': 0.0,
            'final_research_question': '',
            'feasibility_status': 'LOW',
            'conversation_summary': '',
            'last_analysis_sequence_number': 0
        }
    )
    return initiation_data
