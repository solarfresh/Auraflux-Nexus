"""
Workflow Views Module
This module organizes views by ISP (Information Search Process) stages.
"""

# Base / Shared Views
# These views are stage-agnostic (e.g., chat history is used everywhere)
from .base import (ChatHistoryEntryView, ReflectionLogView,
                   SessionReflectionLogView)
# # Initiation Stage Views
# # Specifically for Topic Definition & Lock-in
from .initiation import (RefinedTopicView, SessionTopicKeywordView,
                         SessionTopicScopeElementView, WorkflowChatInputView)

# # Exploration Stage Views (Placeholders for next phase)
# # Specifically for Canvas & Resource Mapping
# # from .exploration import (
# #     CanvasLayoutView,
# #     ResourceNodeMappingView
# # )

__all__ = [
    'ChatHistoryEntryView',
    'ReflectionLogView',
    'RefinedTopicView',
    'SessionReflectionLogView',
    'SessionTopicKeywordView',
    'SessionTopicScopeElementView',
    'TopicKeywordView',
    'TopicScopeElementView',
    'WorkflowChatInputView',
]
