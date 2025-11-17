from adrf.views import APIView
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import WorkflowState
from .serializers import WorkflowStateSerializer

User = get_user_model()


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