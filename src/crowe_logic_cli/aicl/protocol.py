# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""
AICL Protocol Definition

Defines the structured message format for AI-to-AI communication.
Enables models to exchange context, reasoning, critiques, and synthesis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class AICLRole(str, Enum):
    """Role of the AI agent in the conversation."""
    INITIATOR = "initiator"      # Starts the task
    RESPONDER = "responder"      # Responds to initiator
    REVIEWER = "reviewer"        # Reviews/critiques work
    SYNTHESIZER = "synthesizer"  # Combines multiple perspectives
    VALIDATOR = "validator"      # Fact-checks and validates
    EXECUTOR = "executor"        # Executes code/actions
    ORCHESTRATOR = "orchestrator"  # Human or system coordinator


class AICLIntent(str, Enum):
    """Intent of the message - what action is being performed."""
    # Primary intents
    QUERY = "query"              # Asking a question
    RESPONSE = "response"        # Answering a query
    PROPOSAL = "proposal"        # Proposing a solution
    CRITIQUE = "critique"        # Critiquing a proposal
    REVISION = "revision"        # Revised proposal after critique
    SYNTHESIS = "synthesis"      # Combining multiple perspectives
    VALIDATION = "validation"    # Confirming correctness
    REJECTION = "rejection"      # Rejecting with reasoning

    # Code-specific intents
    CODE_GENERATE = "code_generate"
    CODE_REVIEW = "code_review"
    CODE_FIX = "code_fix"
    CODE_OPTIMIZE = "code_optimize"
    CODE_EXPLAIN = "code_explain"

    # Research intents
    RESEARCH = "research"
    FACT_CHECK = "fact_check"
    CITE_SOURCES = "cite_sources"

    # Debate intents
    ARGUE_FOR = "argue_for"
    ARGUE_AGAINST = "argue_against"
    CONCEDE = "concede"
    COUNTER = "counter"

    # Meta intents
    CLARIFY = "clarify"
    DELEGATE = "delegate"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class AICLContext:
    """
    Shared context between AI agents.
    Contains all information needed for coherent multi-model reasoning.
    """
    task_id: str = field(default_factory=lambda: str(uuid4()))
    original_prompt: str = ""
    current_objective: str = ""
    constraints: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)  # code, data, etc.
    confidence_required: float = 0.8
    max_iterations: int = 5
    current_iteration: int = 0
    consensus_reached: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_artifact(self, key: str, value: Any, artifact_type: str = "text") -> None:
        """Add an artifact to the shared context."""
        self.artifacts[key] = {
            "value": value,
            "type": artifact_type,
            "added_at": datetime.utcnow().isoformat(),
        }

    def get_artifact(self, key: str) -> Any:
        """Retrieve an artifact value."""
        if key in self.artifacts:
            return self.artifacts[key]["value"]
        return None


@dataclass
class AICLMessage:
    """
    A single message in the AICL protocol.
    Structured for AI-to-AI understanding and processing.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Identity
    sender_model: str = ""  # e.g., "claude-opus-4-5", "gpt-5.1-codex"
    sender_role: AICLRole = AICLRole.RESPONDER

    # Content
    intent: AICLIntent = AICLIntent.RESPONSE
    content: str = ""
    reasoning: str = ""  # Chain-of-thought explanation

    # Confidence and quality
    confidence: float = 0.0  # 0.0 to 1.0
    quality_signals: dict[str, float] = field(default_factory=dict)

    # References
    references_message_id: Optional[str] = None  # Reply to specific message
    artifacts_modified: list[str] = field(default_factory=list)

    # Structured data
    code_blocks: list[dict[str, str]] = field(default_factory=list)
    citations: list[dict[str, str]] = field(default_factory=list)

    def to_prompt(self) -> str:
        """Convert to a prompt string for the receiving model."""
        lines = [
            f"[AICL MESSAGE from {self.sender_model} as {self.sender_role.value}]",
            f"Intent: {self.intent.value}",
            f"Confidence: {self.confidence:.0%}",
            "",
            "Content:",
            self.content,
        ]

        if self.reasoning:
            lines.extend(["", "Reasoning:", self.reasoning])

        if self.code_blocks:
            lines.append("")
            for block in self.code_blocks:
                lang = block.get("language", "")
                code = block.get("code", "")
                lines.append(f"```{lang}\n{code}\n```")

        lines.append("[/AICL MESSAGE]")
        return "\n".join(lines)


@dataclass
class AICLConversation:
    """
    A complete AICL conversation between multiple AI agents.
    Tracks the full history and shared context.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    context: AICLContext = field(default_factory=AICLContext)
    messages: list[AICLMessage] = field(default_factory=list)

    # Participating models
    models: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Conversation state
    status: str = "active"  # active, paused, completed, failed
    final_output: Optional[str] = None

    def add_model(self, model_id: str, role: AICLRole, provider: str) -> None:
        """Register a participating model."""
        self.models[model_id] = {
            "role": role.value,
            "provider": provider,
            "joined_at": datetime.utcnow().isoformat(),
            "message_count": 0,
        }

    def add_message(self, message: AICLMessage) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        if message.sender_model in self.models:
            self.models[message.sender_model]["message_count"] += 1
        self.context.current_iteration += 1

    def get_messages_by_model(self, model_id: str) -> list[AICLMessage]:
        """Get all messages from a specific model."""
        return [m for m in self.messages if m.sender_model == model_id]

    def get_messages_by_intent(self, intent: AICLIntent) -> list[AICLMessage]:
        """Get all messages with a specific intent."""
        return [m for m in self.messages if m.intent == intent]

    def build_context_for_model(self, target_model: str) -> str:
        """
        Build a context string for a model, including relevant conversation history.
        """
        lines = [
            "=== AICL CONVERSATION CONTEXT ===",
            f"Task ID: {self.context.task_id}",
            f"Objective: {self.context.current_objective}",
            f"Iteration: {self.context.current_iteration}/{self.context.max_iterations}",
            "",
            "Original Prompt:",
            self.context.original_prompt,
            "",
            "Participating Models:",
        ]

        for model_id, info in self.models.items():
            marker = " (you)" if model_id == target_model else ""
            lines.append(f"  - {model_id}{marker}: {info['role']}")

        if self.context.constraints:
            lines.extend(["", "Constraints:"])
            for c in self.context.constraints:
                lines.append(f"  - {c}")

        lines.extend(["", "=== CONVERSATION HISTORY ===", ""])

        for msg in self.messages[-10:]:  # Last 10 messages for context
            lines.append(msg.to_prompt())
            lines.append("")

        lines.append("=== YOUR TURN ===")
        return "\n".join(lines)
