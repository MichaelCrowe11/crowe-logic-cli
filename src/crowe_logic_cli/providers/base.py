from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Sequence, TypedDict


Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


@dataclass(frozen=True)
class UsageInfo:
    """Token usage information."""
    input_tokens: int
    output_tokens: int
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class ChatResponse:
    content: str
    usage: Optional[UsageInfo] = None


class ChatProvider:
    def name(self) -> str:
        raise NotImplementedError

    def chat(self, messages: Sequence[Message]) -> ChatResponse:
        raise NotImplementedError

    def chat_stream(self, messages: Sequence[Message]):
        """Stream chat response chunks. Yields strings. Optional - not all providers support streaming."""
        raise NotImplementedError("Streaming not supported by this provider")

    def chat_completion_stream(self, messages: Sequence[Message]):
        """Alias for chat_stream for compatibility."""
        return self.chat_stream(messages)

    def stream(self, messages: Sequence[Message]):
        """Alias for chat_stream for compatibility."""
        return self.chat_stream(messages)

    def chat_completion(self, messages: Sequence[Message]) -> str:
        """Alias for chat that returns just the content string."""
        response = self.chat(messages)
        return response.content


def coerce_messages(user_text: str, system: Optional[str] = None) -> list[Message]:
    messages: list[Message] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_text})
    return messages


def get_provider(config) -> ChatProvider:
    """Get a configured chat provider instance.

    This is a convenience wrapper around create_provider from factory.
    """
    from crowe_logic_cli.providers.factory import create_provider
    return create_provider(config)

