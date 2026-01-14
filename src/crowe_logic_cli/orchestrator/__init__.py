# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""
Multi-Model Orchestrator

Coordinates AI agents across multiple providers (Anthropic, OpenAI)
using the AICL protocol for structured communication.
"""

from .multi_client import MultiModelClient, ModelConfig
from .engine import OrchestrationEngine, OrchestrationMode
from .modes import DebateMode, VerifyMode, ParallelMode, ChainMode

__all__ = [
    "MultiModelClient",
    "ModelConfig",
    "OrchestrationEngine",
    "OrchestrationMode",
    "DebateMode",
    "VerifyMode",
    "ParallelMode",
    "ChainMode",
]
