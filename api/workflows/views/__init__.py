"""
Workflow Views Module
This module organizes views by ISP (Information Search Process) stages.
"""

# Base / Shared Views
# These views are stage-agnostic (e.g., chat history is used everywhere)
from .base import (ChatHistoryEntryView, ReflectionLogView,
                   SessionReflectionLogView)
# Initiation Stage Views
# Specifically for Topic Definition & Lock-in
from .initiation import (RefinedTopicView, SessionTopicKeywordView,
                         SessionTopicScopeElementView, WorkflowChatInputView)

# Exploration Stage Views (Placeholders for next phase)
# Specifically for Canvas & Resource Mapping
from .exploration import (
    ExplorationPhaseDataView,
    SidebarRegistryInfoView,
)

__all__ = [
    # base
    'ChatHistoryEntryView',
    'ReflectionLogView',
    'SessionReflectionLogView',
    # initiation
    'RefinedTopicView',
    'SessionTopicKeywordView',
    'SessionTopicScopeElementView',
    'WorkflowChatInputView',
    # exploration
    'ExplorationPhaseDataView',
    'SidebarRegistryInfoView'
]
