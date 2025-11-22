import logging

from adrf.views import APIView
from core.utils import get_user_search_cache_key
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import KnowledgeSource, WorkflowState
from .serializers import (DataLockSerializer, DichotomySuggestionSerializer,
                          WorkflowStateSerializer)
from .tasks import dispatch_agent_task
from .utils import (get_and_persist_cached_results,
                    get_or_create_workflow_state, update_workflow_state)

User = get_user_model()


class DataLockAPIView(APIView):
    """
    Signals the finalization of the Knowledge Base setup
    and atomically transitions the workflow step from 'SEARCH' to 'SCOPE'.
    """
    permission_classes = [IsAuthenticated]

    async def post(self, request, *args, **kwargs):
        user = request.user
        query = request.data.get('query', '').strip()

        if not query:
            return Response({"error": "Query parameter is required."}, status=400)

        # Retrieve the Workflow State
        try:
            workflow_state = await get_or_create_workflow_state(user)
        except Exception:
            # Handle case where user has no state (shouldn't happen if state is created on user login/signup)
            logging.error("Failed to retrieve or create workflow state for user ID %s", user.id)
            return Response(
                {"error": "Could not retrieve or create workflow state."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Check Preconditions
        if workflow_state.current_step != 'SEARCH':
            return Response(
                {"error": f"Data Lock is only allowed in the SEARCH step. Current step: {workflow_state.current_step}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache_key = get_user_search_cache_key(user.id)

        try:
            data_persisted = await get_and_persist_cached_results(user, cache_key)
        except Exception as e:
            # Catch database or transactional errors from within the utility
            return Response(
                {"error": f"Database transaction failed during data lock: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Final Validation Check (Did the cache contain data?)
        if not data_persisted:
            return Response(
                {"error": "Cannot lock data. No search results found in temporary storage (cache). Please run a search first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrieve the updated state for the response (The utility already changed it to 'SCOPE')
        try:
            updated_state = await update_workflow_state(user, query=query)
        except Exception as e:
            logging.error("Failed to retrieve updated workflow state after data lock: %s", str(e))
            return Response(
                {"error": "Failed to retrieve updated workflow state after data lock."},)

        # Return Success Response
        serializer = DataLockSerializer(data={'success': True})
        serializer.is_valid(raise_exception=True)

        return Response(
            {"message": "Knowledge Base locked successfully.", "new_step": updated_state.current_step},
            status=status.HTTP_200_OK
        )


class DichotomySuggestionAPIView(APIView):
    """
    Retrieves dynamically suggested strategic dichotomies (tensions)
    based on the user's locked KnowledgeSource search results.
    """
    permission_classes = [IsAuthenticated]

    # Making this method async prepares it for the actual RAG/computation logic later
    async def get(self, request, *args, **kwargs):
        user = request.user

        # Retrieve the current Workflow State
        try:
            workflow_state = await get_or_create_workflow_state(user)
        except WorkflowState.DoesNotExist:
            return Response(
                {"error": "Workflow state not found. Please start a search first."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check Precondition
        # Dichotomies should only be suggested once the data is locked and step is 'SCOPE'
        if workflow_state.current_step not in ['SCOPE', 'COLLECTION']:
            return Response(
                {"error": f"Dichotomy suggestion is only available in the 'SCOPE' step. Current step: {workflow_state.current_step}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check Cache (The primary read operation)
        if workflow_state.suggested_dichotomies_cache:
            # Data is already computed and cached. Return it immediately.
            suggestions = workflow_state.suggested_dichotomies_cache
            serializer = DichotomySuggestionSerializer(suggestions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Cache Miss: Trigger Asynchronous Computation

        # We need the source text to pass to the agent, but we must handle the case
        # where KnowledgeSource records are not present (which should be caught
        # by the DataLock API, but is a safe check here).
        try:
            # Fetch all snippets from the locked knowledge sources
            knowledge_sources_qs = KnowledgeSource.objects.filter(workflow_state=workflow_state)
            knowledge_sources_text = "\n\n---\n\n".join(
                [ks async for ks in knowledge_sources_qs.values_list('snippet', flat=True)]
            )
        except Exception as e:
            logging.error("Failed to fetch knowledge sources for workflow state %s: %s", workflow_state.id, str(e))
            return Response(
                {"error": "Failed to retrieve required knowledge base data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not knowledge_sources_text.strip():
            return Response(
                {"error": "No locked knowledge sources found to generate suggestions from."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Launch the Decoupled Dispatcher Task
        # This task will run the GenericAgent with the specific configuration
        # and write the result back to workflow_state.suggested_dichotomies_cache.
        dispatch_agent_task.delay(  # Access the task if dispatch_agent_task is a list
            agent_role_name="DichotomySuggester",
            workflow_state_id=workflow_state.user,  # Use the actual workflow state ID
            input_data=knowledge_sources_text
        )

        suggestions = [
            {
                "id": "speed_security",
                "name": "Speed vs. Security",
                "description": "Balancing rapid deployment/iteration with robust defense and compliance.",
                "roles": ["CTO (Speed Focus)", "Legal/Ethics Agent (Security Focus)", "Strategy Analyst"],
            },
            {
                "id": "innovation_regulation",
                "name": "Innovation vs. Regulation",
                "description": "Pushing boundaries with new tech versus maintaining strict adherence to rules.",
                "roles": ["Head of R&D", "Chief Compliance Officer", "Finance Director"],
            },
            {
                "id": "centralization_autonomy",
                "name": "Centralization vs. Autonomy",
                "description": "Managing control/efficiency from HQ versus empowering local team decision-making.",
                "roles": ["COO", "Regional Manager", "HR Lead"],
            },
        ]

        # Serialize and Return
        serializer = DichotomySuggestionSerializer(suggestions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkflowStateView(APIView):
    """
    Retrieves the current workflow state for the authenticated user.
    If no state exists, returns the default initial state.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            # 1. Attempt to retrieve the existing state for the user
            workflow_state = WorkflowState.objects.get(user=user)

            # 2. Serialize and return the saved state
            serializer = WorkflowStateSerializer(workflow_state)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except WorkflowState.DoesNotExist:
            # 3. If no state exists, return the default initial state structure

            # Create a temporary, unsaved default instance
            # default_state = WorkflowState(user=user)
            default_state = WorkflowState(user=user)

            # Serialize the default instance to get the desired JSON structure
            # (current_step='SEARCH', all data fields empty/default dicts)
            serializer = WorkflowStateSerializer(default_state)

            # We return the data but use HTTP 200 OK since this is expected behavior
            return Response(serializer.data, status=status.HTTP_200_OK)