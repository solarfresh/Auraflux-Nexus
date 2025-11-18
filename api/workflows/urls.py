from django.urls import path
from workflows.views import DataLockAPIView, WorkflowStateView


urlpatterns = [
    path('lock-data/', DataLockAPIView.as_view(), name='workflow-data-lock'),
    path('fetch-state/', WorkflowStateView.as_view(), name='workflow-fetch-state'),
]
