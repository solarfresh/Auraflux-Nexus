from canvases.views import ConceptualNodesRecommendationView
from django.urls import path
from projects.views import (ChatHistoryEntryView, ConceptualNodeView,
                            ExplorationPhaseDataView, ProjectChatInputView,
                            ProjectDetailView, ProjectView)

urlpatterns = [
    path('', ProjectView.as_view(), name='project'),
    path('<uuid:project_id>/', ProjectDetailView().as_view(), name='project-detail'),
    path('<uuid:project_id>/nodes/', ConceptualNodeView.as_view(), name='project-nodes'),
    path('<uuid:project_id>/consultation/chat/', ProjectChatInputView.as_view(), name='project-chat-input'),
    path('<uuid:project_id>/consultation/chat/history/', ChatHistoryEntryView.as_view(), name='project-chat-history'),
    path('<uuid:project_id>/exploration/<uuid:canvas_id>/nodes/recommend/', ConceptualNodesRecommendationView().as_view(), name='ConceptualNodesRecommendationView'),
    path('<uuid:project_id>/exploration/session/', ExplorationPhaseDataView().as_view(), name='project-exploration-phase-data'),
]
