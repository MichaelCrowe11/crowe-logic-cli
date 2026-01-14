# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""AICL Serialization - Convert AICL objects to/from JSON."""

import json
from dataclasses import asdict
from typing import Any

from .protocol import (
    AICLMessage,
    AICLRole,
    AICLIntent,
    AICLContext,
    AICLConversation,
)


class AICLSerializer:
    """Serialize and deserialize AICL protocol objects."""

    @staticmethod
    def message_to_dict(msg: AICLMessage) -> dict[str, Any]:
        """Convert an AICLMessage to a dictionary."""
        d = asdict(msg)
        d["sender_role"] = msg.sender_role.value
        d["intent"] = msg.intent.value
        return d

    @staticmethod
    def dict_to_message(d: dict[str, Any]) -> AICLMessage:
        """Convert a dictionary to an AICLMessage."""
        d["sender_role"] = AICLRole(d["sender_role"])
        d["intent"] = AICLIntent(d["intent"])
        return AICLMessage(**d)

    @staticmethod
    def context_to_dict(ctx: AICLContext) -> dict[str, Any]:
        """Convert an AICLContext to a dictionary."""
        return asdict(ctx)

    @staticmethod
    def dict_to_context(d: dict[str, Any]) -> AICLContext:
        """Convert a dictionary to an AICLContext."""
        return AICLContext(**d)

    @staticmethod
    def conversation_to_dict(conv: AICLConversation) -> dict[str, Any]:
        """Convert an AICLConversation to a dictionary."""
        return {
            "id": conv.id,
            "created_at": conv.created_at,
            "context": AICLSerializer.context_to_dict(conv.context),
            "messages": [AICLSerializer.message_to_dict(m) for m in conv.messages],
            "models": conv.models,
            "status": conv.status,
            "final_output": conv.final_output,
        }

    @staticmethod
    def dict_to_conversation(d: dict[str, Any]) -> AICLConversation:
        """Convert a dictionary to an AICLConversation."""
        conv = AICLConversation(
            id=d["id"],
            created_at=d["created_at"],
            context=AICLSerializer.dict_to_context(d["context"]),
            models=d["models"],
            status=d["status"],
            final_output=d.get("final_output"),
        )
        conv.messages = [AICLSerializer.dict_to_message(m) for m in d["messages"]]
        return conv

    @staticmethod
    def to_json(obj: AICLConversation | AICLMessage | AICLContext, indent: int = 2) -> str:
        """Serialize an AICL object to JSON string."""
        if isinstance(obj, AICLConversation):
            return json.dumps(AICLSerializer.conversation_to_dict(obj), indent=indent)
        elif isinstance(obj, AICLMessage):
            return json.dumps(AICLSerializer.message_to_dict(obj), indent=indent)
        elif isinstance(obj, AICLContext):
            return json.dumps(AICLSerializer.context_to_dict(obj), indent=indent)
        raise TypeError(f"Cannot serialize {type(obj)}")

    @staticmethod
    def from_json(json_str: str, obj_type: str = "conversation") -> Any:
        """Deserialize a JSON string to an AICL object."""
        d = json.loads(json_str)
        if obj_type == "conversation":
            return AICLSerializer.dict_to_conversation(d)
        elif obj_type == "message":
            return AICLSerializer.dict_to_message(d)
        elif obj_type == "context":
            return AICLSerializer.dict_to_context(d)
        raise ValueError(f"Unknown object type: {obj_type}")
