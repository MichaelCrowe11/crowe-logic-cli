# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""
Orchestration Engine

Core engine that coordinates multi-model conversations using AICL.
Supports multiple orchestration modes for different use cases.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from ..aicl import (
    AICLMessage,
    AICLRole,
    AICLIntent,
    AICLContext,
    AICLConversation,
)
from .multi_client import MultiModelClient, ModelConfig


class OrchestrationMode(str, Enum):
    """Available orchestration modes."""
    DEBATE = "debate"          # Models argue different perspectives
    VERIFY = "verify"          # One creates, one validates
    PARALLEL = "parallel"      # Both work simultaneously
    CHAIN = "chain"            # Sequential processing
    CONSENSUS = "consensus"    # Iterate until agreement
    SPECIALIZE = "specialize"  # Route to best-suited model


@dataclass
class OrchestrationResult:
    """Result of an orchestration session."""
    conversation: AICLConversation
    final_output: str
    consensus_reached: bool
    iterations: int
    model_contributions: dict[str, int]
    quality_score: float


class BaseOrchestrationMode(ABC):
    """Base class for orchestration modes."""

    def __init__(self, client: MultiModelClient) -> None:
        self.client = client
        self.on_message: Optional[Callable[[AICLMessage], None]] = None
        self.on_progress: Optional[Callable[[str, float], None]] = None

    @abstractmethod
    async def execute(
        self,
        prompt: str,
        models: list[str],
        context: Optional[AICLContext] = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """Execute the orchestration mode."""
        pass

    def emit_message(self, message: AICLMessage) -> None:
        """Emit a message event."""
        if self.on_message:
            self.on_message(message)

    def emit_progress(self, stage: str, progress: float) -> None:
        """Emit a progress event."""
        if self.on_progress:
            self.on_progress(stage, progress)


class OrchestrationEngine:
    """
    Main orchestration engine.
    Manages multi-model conversations and coordinates modes.
    """

    def __init__(self) -> None:
        self.client = MultiModelClient()
        self.modes: dict[OrchestrationMode, BaseOrchestrationMode] = {}
        self.active_conversations: dict[str, AICLConversation] = {}

    def register_mode(self, mode: OrchestrationMode, handler: BaseOrchestrationMode) -> None:
        """Register an orchestration mode handler."""
        self.modes[mode] = handler

    def register_model(self, config: ModelConfig) -> None:
        """Register a model with the client."""
        self.client.register_model(config)

    async def orchestrate(
        self,
        prompt: str,
        mode: OrchestrationMode,
        models: list[str],
        on_message: Optional[Callable[[AICLMessage], None]] = None,
        on_progress: Optional[Callable[[str, float], None]] = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """
        Execute an orchestration session.

        Args:
            prompt: The user's request
            mode: Which orchestration mode to use
            models: List of model IDs to participate
            on_message: Callback for each AICL message
            on_progress: Callback for progress updates
            **kwargs: Mode-specific options

        Returns:
            OrchestrationResult with the final output and conversation
        """
        if mode not in self.modes:
            raise ValueError(f"Mode {mode} not registered")

        handler = self.modes[mode]
        handler.on_message = on_message
        handler.on_progress = on_progress

        context = AICLContext(
            original_prompt=prompt,
            current_objective=prompt,
            max_iterations=kwargs.get("max_iterations", 5),
        )

        result = await handler.execute(prompt, models, context, **kwargs)

        # Store conversation
        self.active_conversations[result.conversation.id] = result.conversation

        return result

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.close()


def create_default_engine() -> OrchestrationEngine:
    """Create an engine with all modes registered."""
    from .modes import DebateMode, VerifyMode, ParallelMode, ChainMode

    engine = OrchestrationEngine()

    # Register modes
    engine.register_mode(OrchestrationMode.DEBATE, DebateMode(engine.client))
    engine.register_mode(OrchestrationMode.VERIFY, VerifyMode(engine.client))
    engine.register_mode(OrchestrationMode.PARALLEL, ParallelMode(engine.client))
    engine.register_mode(OrchestrationMode.CHAIN, ChainMode(engine.client))

    # Register default models
    from .multi_client import CLAUDE_OPUS_45, GPT_51_CODEX, GPT_5_TURBO

    engine.register_model(CLAUDE_OPUS_45)
    engine.register_model(GPT_51_CODEX)
    engine.register_model(GPT_5_TURBO)

    return engine
