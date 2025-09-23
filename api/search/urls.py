from django.urls import path
from search.views import SearchView


urlpatterns = [
    path('results/', SearchView.as_view(), name='search'),
]
