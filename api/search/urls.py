from django.urls import path
from search.views import AssistantPanelView, SearchView


urlpatterns = [
    path('assistant/', AssistantPanelView.as_view(), name='search-assistant'),
    path('results/', SearchView.as_view(), name='search-results'),
]
