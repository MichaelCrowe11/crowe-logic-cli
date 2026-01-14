# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""
AICL - AI Communication Language

A structured protocol for AI-to-AI communication enabling multi-model
orchestration, debate, verification, and collaborative reasoning.
"""

from .protocol import (
    AICLMessage,
    AICLRole,
    AICLIntent,
    AICLContext,
    AICLConversation,
)
from .serializer import AICLSerializer

__all__ = [
    "AICLMessage",
    "AICLRole",
    "AICLIntent",
    "AICLContext",
    "AICLConversation",
    "AICLSerializer",
]
