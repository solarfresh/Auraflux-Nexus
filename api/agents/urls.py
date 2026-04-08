from agents.views import (AgentConfigDetailView, AgentConfigView,
                          ModelProviderAvailableView, ModelProviderDetailView,
                          ModelProviderView)
from django.urls import path

urlpatterns = [
    path('', AgentConfigView.as_view(), name='agent-config'),
    path('<uuid:agent_id>/', AgentConfigDetailView().as_view(), name='agent-config-detail'),
    path('models/', ModelProviderView.as_view(), name='model-provider'),
    path('models/available/', ModelProviderAvailableView.as_view(), name='model-available'),
    path('models/<uuid:provider_id>/', ModelProviderDetailView.as_view(), name='model-provider-detail'),
]
