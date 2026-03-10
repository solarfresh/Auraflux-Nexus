from django.urls import path
from workflows.views import (ChatHistoryEntryView,
                             ConceptualNodesRecommendationView,
                             ExplorationPhaseDataView, RefinedTopicView,
                             ReflectionLogView, SessionReflectionLogView,
                             SessionTopicKeywordView,
                             SessionTopicScopeElementView,
                             SidebarRegistryInfoView, WorkflowChatInputView)

urlpatterns = [
    path('reflection/<uuid:log_id>/', ReflectionLogView.as_view(), name='reflection-log'),
    path('<uuid:workflow_id>/keywords/', SessionTopicKeywordView.as_view(), name='workflow-topic-keyword'),
    path('<uuid:workflow_id>/reflection/', SessionReflectionLogView.as_view(), name='workflow-reflection'),
    path('<uuid:workflow_id>/scopes/', SessionTopicScopeElementView.as_view(), name='workflow-topic-scope-element'),
    path('<uuid:workflow_id>/initiation/chat/', WorkflowChatInputView.as_view(), name='workflow-chat-input'),
    path('<uuid:workflow_id>/initiation/chat/history/', ChatHistoryEntryView.as_view(), name='workflow-chat-history'),
    path('<uuid:workflow_id>/initiation/topic/', RefinedTopicView.as_view(), name='workflow-refined-topic'),
    path('<uuid:workflow_id>/exploration/<uuid:canvas_id>/nodes/', ConceptualNodesRecommendationView().as_view(), name='ConceptualNodesRecommendationView'),
    path('<uuid:workflow_id>/exploration/session/', ExplorationPhaseDataView().as_view(), name='workflow-exploration-phase-data'),
    path('<uuid:workflow_id>/exploration/sidebar/', SidebarRegistryInfoView().as_view(), name='workflow-sidebar-registry-info'),
]
