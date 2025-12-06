from typing import TYPE_CHECKING
from uuid import UUID

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import InitiationPhaseData, ResearchWorkflowState

if TYPE_CHECKING:
    from users.models import User
else:
    User = get_user_model()


@sync_to_async
def atomic_read_and_lock_initiation_data(session_id: UUID, user_id: int) -> tuple[ResearchWorkflowState, InitiationPhaseData]:
    """
    Executes a single atomic transaction to lock the state and load the initiation data.
    This is the function called by the WorkflowChatInputView.
    """

    # Ensures the entire sequence is locked and atomic
    with transaction.atomic():
        # Retrieve and LOCK the main state
        # Note: Must use select_for_update() for locking
        workflow_state = get_object_or_404(
            ResearchWorkflowState.objects.select_for_update(),
            session_id=session_id,
            user_id=user_id
        )

        # Retrieve or Create and LOCK the phase data
        # We need to get or create the InitiationPhaseData instance.
        # Since it is a OneToOne relationship, the lock on the parent often suffices,
        # but select_for_update() is safer if the instance exists.

        # We call the synchronous helper function *within* the atomic block
        initiation_data = get_or_create_initiation_data(workflow_state)

        # Manually lock the data instance if necessary (complex locking is usually done via raw query or dedicated manager)
        # initiation_data = InitiationPhaseData.objects.select_for_update().get(workflow_state=workflow_state)

        return workflow_state, initiation_data

@sync_to_async
def get_refined_topic_instance(session_id: UUID):
    initiation_instance = InitiationPhaseData.objects.select_related(
        'workflow_state',
        'latest_reflection_entry'
    ).prefetch_related(
        'keywords_list',
        'scope_elements_list'
    ).get(
        workflow_state__session_id=session_id
    )

    return initiation_instance

@sync_to_async
def create_workflow_state(session_id: UUID, user_id: int, initial_stage: str) -> ResearchWorkflowState:
    """
    Creates a new ResearchWorkflowState instance.
    """
    return ResearchWorkflowState.objects.create(
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

@sync_to_async
def get_workflow_state(session_id: UUID, user_id: int) -> ResearchWorkflowState:
    """
    Retrieves an existing ResearchWorkflowState instance.
    If not found, it raises a DoesNotExist exception (for 404 handling in the View).
    """
    # Note: Use get_object_or_404 in the View or handle the DoesNotExist here.
    return ResearchWorkflowState.objects.get(
        session_id=session_id,
        user_id=user_id
    )

def get_or_create_initiation_data(workflow_state: ResearchWorkflowState) -> InitiationPhaseData:
    """
    Retrieves or creates the InitiationPhaseData linked to the workflow state.
    Handles phase-specific default value initialization.

    NOTE: Don't be decorate this function with @sync_to_async.
    This function is used by atomic_read_and_lock_initiation_data and is
    intended to be called within an atomic transaction.
    """
    # Using get_or_create to safely handle the OneToOne relationship
    initiation_data, created = InitiationPhaseData.objects.get_or_create(
        workflow_state=workflow_state,
        defaults={
            'clarity_score': 0.0,
            'last_da_execution_time': timezone.now(),
            'keyword_stability_count': 0,
            'chat_history': []
        }
    )
    return initiation_data
