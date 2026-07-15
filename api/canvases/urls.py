from django.urls import path

from .views import (ConceptualCanvasView, ConceptualEdgeCreateView,
                    ConceptualEdgesRecommendationView, ConceptualEdgeView,
                    ConceptualNodeCreateView, ConceptualNodeView)

urlpatterns = [
    path('<uuid:canvas_id>/', ConceptualCanvasView.as_view(), name='canvas-conceptual-graph'),
    path('<uuid:canvas_id>/edges/', ConceptualEdgeCreateView.as_view(), name='canvas-edge-create'),
    path('<uuid:canvas_id>/edges/recommend/', ConceptualEdgesRecommendationView.as_view(), name='canvas-edge-recommendation'),
    path('<uuid:canvas_id>/edges/<uuid:edge_id>/', ConceptualEdgeView.as_view(), name='canvas-edge'),
    path('<uuid:canvas_id>/nodes/', ConceptualNodeCreateView.as_view(), name='canvas-node-create'),
    path('<uuid:canvas_id>/nodes/<uuid:node_id>/', ConceptualNodeView.as_view(), name='canvas-node-relation'),
]