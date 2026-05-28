"""Conversation context management for the coding agent."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..llm.message import Message, Role


@dataclass
class ConversationContext:
    """Manages conversation history and context for the agent.

    Provides context window management and optional persistence.

    Attributes:
        messages: List of conversation messages.
        max_length: Maximum number of messages to retain.
        system_prompt: Optional system prompt for the conversation.
        history_file: Optional path for persisting conversation history.
        session_context: Optional session context prepared before starting.
    """

    messages: list[Message] = field(default_factory=list)
    max_length: int = 100
    system_prompt: Optional[str] = None
    history_file: Optional[Path] = None
    session_context: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize context after dataclass initialization."""
        if self.system_prompt:
            self.add_message(Message(role=Role.SYSTEM, content=self.system_prompt))

        # Add session context as a system message if provided
        if self.session_context:
            self.add_message(Message(role=Role.SYSTEM, content=self.session_context))

        if self.history_file:
            self._load_history()

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation.

        Args:
            message: Message to add.
        """
        self.messages.append(message)
        self._trim_if_needed()

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation.

        Args:
            content: Message content.
        """
        self.add_message(Message(role=Role.USER, content=content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation.

        Args:
            content: Message content.
        """
        self.add_message(Message(role=Role.ASSISTANT, content=content))

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        """Add a tool result message.

        Args:
            tool_call_id: ID of the tool call this result corresponds to.
            content: Result content.
        """
        self.add_message(
            Message(role=Role.TOOL, content=content, tool_call_id=tool_call_id)
        )

    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message from the conversation.

        Returns:
            Content of the last user message, or None if no user message exists.
        """
        for msg in reversed(self.messages):
            if msg.role == Role.USER:
                return msg.content
        return None

    def remove_last_user_message(self) -> bool:
        """Remove the last user message and any subsequent messages.

        This is useful for retrying the last task by removing it from history
        so it can be re-processed.

        Returns:
            True if a user message was removed, False otherwise.
        """
        # Find the last user message index
        last_user_idx = -1
        for i, msg in enumerate(self.messages):
            if msg.role == Role.USER:
                last_user_idx = i

        if last_user_idx == -1:
            return False

        # Remove the last user message and all messages after it
        # (including assistant responses and tool results)
        self.messages = self.messages[:last_user_idx]
        return True

    def get_messages(self) -> list[Message]:
        """Get all messages in the conversation.

        Returns:
            List of messages.
        """
        return self.messages.copy()

    def clear(self) -> None:
        """Clear the conversation history."""
        self.messages.clear()
        if self.system_prompt:
            self.add_message(Message(role=Role.SYSTEM, content=self.system_prompt))
        self._save_history()

    def _trim_if_needed(self) -> None:
        """Trim messages if exceeding max length."""
        if len(self.messages) > self.max_length:
            # Keep system message and last N messages
            system_msg = None
            if self.messages and self.messages[0].role == Role.SYSTEM:
                system_msg = self.messages[0]

            self.messages = self.messages[-(self.max_length - 1):]

            if system_msg:
                self.messages.insert(0, system_msg)

    def _save_history(self) -> None:
        """Save conversation history to file."""
        if not self.history_file:
            return

        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "messages": [msg.to_dict() for msg in self.messages],
                "system_prompt": self.system_prompt,
            }
            self.history_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            import logging
            logging.warning(f"Failed to save conversation history: {e}")

    def _load_history(self) -> None:
        """Load conversation history from file."""
        if not self.history_file or not self.history_file.exists():
            return

        try:
            data = json.loads(self.history_file.read_text())
            self.messages = [Message.from_dict(m) for m in data.get("messages", [])]
            self._trim_if_needed()
        except Exception as e:
            import logging
            logging.warning(f"Failed to load conversation history: {e}")

    def token_estimate(self) -> int:
        """Estimate token count for current context.

        This is a rough estimate; actual tokenization depends on the model.

        Returns:
            Estimated token count.
        """
        total = 0
        for msg in self.messages:
            # Rough estimate: 1 token ≈ 4 characters
            total += len(msg.content) // 4
            total += 4  # Overhead per message
        return total
