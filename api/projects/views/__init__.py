"""
Project Views Module
This module organizes views by ISP (Information Search Process) stages.
"""

# Base / Shared Views
# These views are stage-agnostic (e.g., chat history is used everywhere)
from .base import (ChatHistoryEntryView, ProjectDetailView, ProjectView,
                   ReflectionLogView, SessionReflectionLogView)
# Exploration Stage Views (Placeholders for next phase)
# Specifically for Canvas & Resource Mapping
from .exploration import (ConceptualNodesRecommendationView,
                          ExplorationPhaseDataView, SidebarRegistryInfoView)
# Initiation Stage Views
# Specifically for Topic Definition & Lock-in
from .initiation import (ProjectChatInputView, RefinedTopicView,
                         SessionTopicKeywordView, SessionTopicScopeElementView)

__all__ = [
    # base
    'ChatHistoryEntryView',
    'ProjectView',
    'ProjectDetailView',
    'ReflectionLogView',
    'SessionReflectionLogView',
    # initiation
    'RefinedTopicView',
    'SessionTopicKeywordView',
    'SessionTopicScopeElementView',
    'ProjectChatInputView',
    # exploration
    'ConceptualNodesRecommendationView',
    'ExplorationPhaseDataView',
    'SidebarRegistryInfoView'
]
