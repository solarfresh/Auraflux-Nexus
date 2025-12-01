from django.urls import path
from workflows.views import WorkflowChatInputView

urlpatterns = [
    path('<uuid:session_id>/chat', WorkflowChatInputView.as_view(), name='workflow-chat-input'),
]
