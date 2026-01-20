from types import SimpleNamespace
from typing import Dict
from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from workflows.models import InitiationPhaseData, ResearchWorkflow
from workflows.utils.base import get_resource_suggestion


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
        initiation_data = InitiationPhaseData.objects.select_for_update().get(workflow=workflow)

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

def determine_feasibility_status(score: int, is_niche: bool) -> str:
    """Helper function to determine the final Feasibility Status based on Agent output and rules."""
    if is_niche or score < 4:
        return 'LOW'
    if score >= 8:
        return 'HIGH'
    return 'MEDIUM'

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
