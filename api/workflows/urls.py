from django.urls import path
from workflows.views import (DataLockAPIView, DichotomySuggestionAPIView,
                             WorkflowStateView)

urlpatterns = [
    path('dichotomies/', DichotomySuggestionAPIView.as_view(), name='workflow-dichotomies-suggestion'),
    path('fetch-state/', WorkflowStateView.as_view(), name='workflow-fetch-state'),
    path('lock-data/', DataLockAPIView.as_view(), name='workflow-data-lock'),
]
