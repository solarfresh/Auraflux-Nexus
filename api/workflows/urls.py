from django.urls import path
from workflows.views import (ChatHistoryEntryView, RefinedTopicView,
                             ReflectionLogView, SessionReflectionLogView,
                             SessionTopicKeywordView,
                             SessionTopicScopeElementView, TopicKeywordView,
                             TopicScopeElementView, WorkflowChatInputView)

urlpatterns = [
    path('<uuid:session_id>/chat/', WorkflowChatInputView.as_view(), name='workflow-chat-input'),
    path('<uuid:session_id>/chat/history/', ChatHistoryEntryView.as_view(), name='workflow-chat-history'),
    path('<uuid:session_id>/topic/', RefinedTopicView.as_view(), name='workflow-refined-topic'),
    path('<uuid:session_id>/keywords/', SessionTopicKeywordView.as_view(), name='workflow-topic-keyword'),
    path('<uuid:session_id>/reflection/', SessionReflectionLogView.as_view(), name='workflow-reflection'),
    path('<uuid:session_id>/scopes/', SessionTopicScopeElementView.as_view(), name='workflow-topic-scope-element'),
]

keyword_urlpatterns = [
    path('<uuid:keyword_id>/', TopicKeywordView.as_view(), name='topic-keyword'),
]

log_urlpatterns = [
    path('<uuid:log_id>/', ReflectionLogView.as_view(), name='reflection-log'),
]

scope_urlpatterns = [
    path('<uuid:scope_id>/', TopicScopeElementView.as_view(), name='topic-scope-element'),
]