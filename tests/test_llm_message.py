"""Tests for the message types and LLM client."""

import pytest

from coding_agent.llm.message import Message, Role, ToolCall


class TestRole:
    """Tests for the Role enumeration."""

    def test_role_values(self):
        """Test that role values are correct."""
        assert Role.SYSTEM.value == "system"
        assert Role.USER.value == "user"
        assert Role.ASSISTANT.value == "assistant"
        assert Role.TOOL.value == "tool"

    def test_role_from_string(self):
        """Test creating roles from strings."""
        assert Role("system") == Role.SYSTEM
        assert Role("user") == Role.USER
        assert Role("assistant") == Role.ASSISTANT
        assert Role("tool") == Role.TOOL


class TestMessage:
    """Tests for the Message dataclass."""

    def test_create_simple_message(self):
        """Test creating a simple message with required fields."""
        msg = Message(role=Role.USER, content="Hello")
        assert msg.role == Role.USER
        assert msg.content == "Hello"
        assert msg.name is None
        assert msg.tool_call_id is None

    def test_create_message_with_optional_fields(self):
        """Test creating a message with optional fields."""
        msg = Message(
            role=Role.TOOL,
            content="Result",
            name="my_tool",
            tool_call_id="call_123",
        )
        assert msg.role == Role.TOOL
        assert msg.content == "Result"
        assert msg.name == "my_tool"
        assert msg.tool_call_id == "call_123"

    def test_message_to_dict_basic(self):
        """Test converting basic message to dictionary."""
        msg = Message(role=Role.USER, content="Test message")
        msg_dict = msg.to_dict()

        assert msg_dict["role"] == "user"
        assert msg_dict["content"] == "Test message"
        assert "name" not in msg_dict
        assert "tool_call_id" not in msg_dict

    def test_message_to_dict_with_optional_fields(self):
        """Test converting message with optional fields to dictionary."""
        msg = Message(
            role=Role.TOOL,
            content="Tool result",
            name="test_tool",
            tool_call_id="call_456",
        )
        msg_dict = msg.to_dict()

        assert msg_dict["role"] == "tool"
        assert msg_dict["content"] == "Tool result"
        assert msg_dict["name"] == "test_tool"
        assert msg_dict["tool_call_id"] == "call_456"

    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        data = {
            "role": "assistant",
            "content": "Response text",
        }
        msg = Message.from_dict(data)

        assert msg.role == Role.ASSISTANT
        assert msg.content == "Response text"

    def test_message_from_dict_with_optional_fields(self):
        """Test creating message from dictionary with optional fields."""
        data = {
            "role": "tool",
            "content": "Result",
            "name": "tool_name",
            "tool_call_id": "call_789",
        }
        msg = Message.from_dict(data)

        assert msg.role == Role.TOOL
        assert msg.content == "Result"
        assert msg.name == "tool_name"
        assert msg.tool_call_id == "call_789"

    def test_message_roundtrip(self):
        """Test converting message to dict and back."""
        original = Message(
            role=Role.USER,
            content="Roundtrip test",
            name=None,
            tool_call_id=None,
        )
        msg_dict = original.to_dict()
        restored = Message.from_dict(msg_dict)

        assert restored.role == original.role
        assert restored.content == original.content


class TestToolCall:
    """Tests for the ToolCall dataclass."""

    def test_create_tool_call(self):
        """Test creating a tool call."""
        tc = ToolCall(id="call_abc", name="my_function", arguments='{"param": "value"}')

        assert tc.id == "call_abc"
        assert tc.name == "my_function"
        assert tc.arguments == '{"param": "value"}'

    def test_tool_call_to_dict(self):
        """Test converting tool call to dictionary."""
        tc = ToolCall(
            id="call_xyz",
            name="search_files",
            arguments='{"pattern": "*.py"}',
        )
        tc_dict = tc.to_dict()

        assert tc_dict["id"] == "call_xyz"
        assert tc_dict["type"] == "function"
        assert tc_dict["function"]["name"] == "search_files"
        assert tc_dict["function"]["arguments"] == '{"pattern": "*.py"}'

    def test_tool_call_with_empty_arguments(self):
        """Test tool call with empty arguments."""
        tc = ToolCall(id="call_empty", name="list_dir", arguments="")
        tc_dict = tc.to_dict()

        assert tc_dict["function"]["arguments"] == ""

    def test_tool_call_with_json_arguments(self):
        """Test tool call with JSON arguments."""
        import json

        args = {"path": "src", "recursive": True}
        tc = ToolCall(
            id="call_json",
            name="read_file",
            arguments=json.dumps(args),
        )

        parsed_args = json.loads(tc.arguments)
        assert parsed_args["path"] == "src"
        assert parsed_args["recursive"] is True
