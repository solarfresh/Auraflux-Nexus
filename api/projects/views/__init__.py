"""
Project Views Module
This module organizes views by ISP (Information Search Process) stages.
"""

# Base / Shared Views
# These views are stage-agnostic (e.g., chat history is used everywhere)
from .base import ChatHistoryEntryView, ProjectDetailView, ProjectView, ConceptualNodeView
# Exploration Stage Views (Placeholders for next phase)
# Specifically for Canvas & Resource Mapping
from .exploration import ExplorationPhaseDataView
# Consultation Stage Views
# Specifically for Topic Definition & Lock-in
from .consultation import ProjectChatInputView

__all__ = [
    # base
    'ChatHistoryEntryView',
    'ConceptualNodeView',
    'ProjectView',
    'ProjectDetailView',
    # consultation
    'ProjectChatInputView',
    # exploration
    'ExplorationPhaseDataView',
]
