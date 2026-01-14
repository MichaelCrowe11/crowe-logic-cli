# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""
Rich Terminal UI

Beautiful, interactive terminal interface for multi-model orchestration.
Features live updates, split panels, and visual diff comparisons.
"""

from .console import Console, Theme
from .panels import ModelPanel, DebatePanel, ProgressPanel, ConversationPanel
from .live import LiveOrchestration
from .diff import DiffView

__all__ = [
    "Console",
    "Theme",
    "ModelPanel",
    "DebatePanel",
    "ProgressPanel",
    "ConversationPanel",
    "LiveOrchestration",
    "DiffView",
]
