from django.urls import path
from workflows.views import WorkflowStateView


urlpatterns = [
    path('fetch-state/', WorkflowStateView.as_view(), name='workflow-fetch-state'),
]
