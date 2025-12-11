from django.urls import path
from workflows.views import (ChatHistoryEntryView, RefinedTopicView,
                             WorkflowChatInputView, SessionTopicKeywordView, TopicKeywordView)

urlpatterns = [
    path('<uuid:session_id>/chat', WorkflowChatInputView.as_view(), name='workflow-chat-input'),
    path('<uuid:session_id>/chat_history', ChatHistoryEntryView.as_view(), name='workflow-chat-history'),
    path('<uuid:session_id>/refined_topic', RefinedTopicView.as_view(), name='workflow-refined-topic'),
    path('<uuid:session_id>/topic_keywords', SessionTopicKeywordView.as_view(), name='workflow-topic-keyword'),
    path('<uuid:keyword_id>/', TopicKeywordView.as_view(), name='topic-keyword'),
]
