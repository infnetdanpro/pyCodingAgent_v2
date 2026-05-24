"""Message types for LLM communication."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Role(str, Enum):
    """Message role enumeration."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """Represents a single message in the conversation.

    Attributes:
        role: The role of the message sender.
        content: The text content of the message.
        name: Optional name for tool messages.
        tool_call_id: Optional ID linking tool calls and responses.
    """

    role: Role
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert message to dictionary for API consumption.

        Returns:
            Dictionary representation compatible with OpenAI API.
        """
        result: dict = {
            "role": self.role.value,
            "content": self.content,
        }

        if self.name:
            result["name"] = self.name

        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create a Message from a dictionary.

        Args:
            data: Dictionary with message data.

        Returns:
            Message instance.
        """
        return cls(
            role=Role(data["role"]),
            content=data["content"],
            name=data.get("name"),
            tool_call_id=data.get("tool_call_id"),
        )


@dataclass
class ToolCall:
    """Represents a tool call from the LLM.

    Attributes:
        id: Unique identifier for the tool call.
        name: Name of the tool to call.
        arguments: JSON string of arguments for the tool.
    """

    id: str
    name: str
    arguments: str

    def to_dict(self) -> dict:
        """Convert tool call to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }
