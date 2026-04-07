from django.urls import path
from agents.views import AgentConfigDetailView, AgentConfigView, ModelProviderView, ModelProviderDetailView

urlpatterns = [
    path('', AgentConfigView.as_view(), name='agent-config'),
    path('<uuid:agent_id>/', AgentConfigDetailView().as_view(), name='agent-config-detail'),
    path('models/', ModelProviderView.as_view(), name='model-provider'),
    path('models/<uuid:provider_id>/', AgentConfigView.as_view(), name='agent-config'),
]