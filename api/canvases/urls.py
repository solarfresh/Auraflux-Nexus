from django.urls import path
from .views import ConceptualCanvasView

urlpatterns = [
    path('<uuid:canvas_id>/', ConceptualCanvasView.as_view(), name='canvas-conceptual-graph'),
]