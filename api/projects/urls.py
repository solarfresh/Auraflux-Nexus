from django.urls import path
from projects.views import (ChatHistoryEntryView,
                            ConceptualNodesRecommendationView,
                            ExplorationPhaseDataView, ProjectChatInputView,
                            ProjectView, RefinedTopicView, ReflectionLogView,
                            SessionReflectionLogView, SessionTopicKeywordView,
                            SessionTopicScopeElementView,
                            SidebarRegistryInfoView)

urlpatterns = [
    path('reflection/<uuid:log_id>/', ReflectionLogView.as_view(), name='reflection-log'),
    path('', ProjectView.as_view(), name='project'),
    path('<uuid:project_id>/keywords/', SessionTopicKeywordView.as_view(), name='project-topic-keyword'),
    path('<uuid:project_id>/reflection/', SessionReflectionLogView.as_view(), name='project-reflection'),
    path('<uuid:project_id>/scopes/', SessionTopicScopeElementView.as_view(), name='project-topic-scope-element'),
    path('<uuid:project_id>/initiation/chat/', ProjectChatInputView.as_view(), name='project-chat-input'),
    path('<uuid:project_id>/initiation/chat/history/', ChatHistoryEntryView.as_view(), name='project-chat-history'),
    path('<uuid:project_id>/initiation/topic/', RefinedTopicView.as_view(), name='project-refined-topic'),
    path('<uuid:project_id>/exploration/<uuid:canvas_id>/nodes/', ConceptualNodesRecommendationView().as_view(), name='ConceptualNodesRecommendationView'),
    path('<uuid:project_id>/exploration/session/', ExplorationPhaseDataView().as_view(), name='project-exploration-phase-data'),
    path('<uuid:project_id>/exploration/sidebar/', SidebarRegistryInfoView().as_view(), name='project-sidebar-registry-info'),
]
