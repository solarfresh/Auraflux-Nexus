from django.urls import path

from .views import TopicKeywordView, TopicScopeElementView

urlpatterns = [
    path('keywords/<uuid:keyword_id>/', TopicKeywordView.as_view(), name='topic-keyword'),
    path('scopes/<uuid:scope_id>/', TopicScopeElementView.as_view(), name='topic-scope-element'),
]