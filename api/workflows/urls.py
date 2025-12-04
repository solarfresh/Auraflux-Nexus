from django.urls import path
from workflows.views import ChatHistoryEntryView, WorkflowChatInputView

urlpatterns = [
    path('<uuid:session_id>/chat_history', ChatHistoryEntryView.as_view(), name='workflow-chat-history'),
    path('<uuid:session_id>/chat', WorkflowChatInputView.as_view(), name='workflow-chat-input'),
]
