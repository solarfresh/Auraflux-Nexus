from django.urls import path
from agents.views import AgentConfigDetailView, AgentConfigView

urlpatterns = [
    path('', AgentConfigView.as_view(), name='agent-config'),
    path('<uuid:agent_id>/', AgentConfigDetailView().as_view(), name='agent-config-detail'),
]