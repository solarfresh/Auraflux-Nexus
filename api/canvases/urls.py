from django.urls import path

from .views import ConceptualCanvasView, ConceptualNodeView

urlpatterns = [
    path('<uuid:canvas_id>/', ConceptualCanvasView.as_view(), name='canvas-conceptual-graph'),
    path('<uuid:canvas_id>/nodes/<uuid:node_id>/', ConceptualNodeView.as_view(), name='canvas-node-relation'),
]