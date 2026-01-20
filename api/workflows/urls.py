from django.urls import path
from workflows.views import (ChatHistoryEntryView, RefinedTopicView,
                             ReflectionLogView, SessionReflectionLogView,
                             SessionTopicKeywordView,
                             SessionTopicScopeElementView,
                             WorkflowChatInputView, SidebarRegistryInfoView)

urlpatterns = [
    path('<uuid:session_id>/chat/', WorkflowChatInputView.as_view(), name='workflow-chat-input'),
    path('<uuid:session_id>/chat/history/', ChatHistoryEntryView.as_view(), name='workflow-chat-history'),
    path('<uuid:session_id>/keywords/', SessionTopicKeywordView.as_view(), name='workflow-topic-keyword'),
    path('<uuid:session_id>/reflection/', SessionReflectionLogView.as_view(), name='workflow-reflection'),
    path('<uuid:session_id>/scopes/', SessionTopicScopeElementView.as_view(), name='workflow-topic-scope-element'),
    path('<uuid:session_id>/initiation/topic/', RefinedTopicView.as_view(), name='workflow-refined-topic'),
    path('<uuid:session_id>/exploration/sidebar/', SidebarRegistryInfoView().as_view(), name='workflow-sidebar-registry-info'),
    path('reflection/<uuid:log_id>/', ReflectionLogView.as_view(), name='reflection-log'),
]
