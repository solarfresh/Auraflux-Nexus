from adrf.views import APIView
from core.utils import get_user_search_cache_key
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import WorkflowState
from .serializers import DataLockSerializer, WorkflowStateSerializer
from .utils import get_or_create_workflow_state, update_workflow_state, get_and_persist_cached_results

User = get_user_model()


class DataLockAPIView(APIView):
    """
    Signals the finalization of the Knowledge Base setup
    and atomically transitions the workflow step from 'SEARCH' to 'SCOPE'.
    """
    permission_classes = [IsAuthenticated]

    async def post(self, request, *args, **kwargs):
        user = request.user

        # Retrieve the Workflow State
        try:
            workflow_state = await get_or_create_workflow_state(user)
        except Exception:
            # Handle case where user has no state (shouldn't happen if state is created on user login/signup)
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
        updated_state = await get_or_create_workflow_state(user)

        # Return Success Response
        serializer = DataLockSerializer(data={'success': True})
        serializer.is_valid(raise_exception=True)

        return Response(
            {"message": "Knowledge Base locked successfully.", "new_step": updated_state.current_step},
            status=status.HTTP_200_OK
        )


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