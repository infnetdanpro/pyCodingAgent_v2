"""Tests for the LLM client implementation."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from coding_agent.config import ModelConfig
from coding_agent.llm.client import LLMClient
from coding_agent.llm.message import Message, Role, ToolCall


class TestLLMClientInitialization:
    """Tests for LLMClient initialization."""

    def test_init_with_default_config(self):
        """Test initializing client with default config."""
        config = ModelConfig()
        client = LLMClient(config)

        assert client.config is config
        assert isinstance(client._client, httpx.Client)

    def test_init_creates_http_client_with_correct_settings(self):
        """Test that HTTP client is configured correctly."""
        config = ModelConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            timeout=30.0,
        )
        client = LLMClient(config)

        assert str(client._client.base_url) == "https://api.example.com"
        # httpx.Timeout object has connect, read, write, pool attributes
        assert client._client.timeout.connect == 30.0


class TestLLMClientContextManager:
    """Tests for LLMClient context manager."""

    def test_context_manager_enter_exit(self):
        """Test using client as a context manager."""
        config = ModelConfig()
        with LLMClient(config) as client:
            assert isinstance(client, LLMClient)

    @patch.object(httpx.Client, "close")
    def test_close_called_on_exit(self, mock_close):
        """Test that close is called when exiting context."""
        config = ModelConfig()
        with LLMClient(config):
            pass
        mock_close.assert_called_once()

    def test_close_method(self):
        """Test explicit close method."""
        config = ModelConfig()
        client = LLMClient(config)
        client.close()
        # Should not raise any exception


class TestLLMClientChat:
    """Tests for LLMClient chat method."""

    @patch.object(httpx.Client, "post")
    def test_chat_success_no_tools(self, mock_post):
        """Test successful chat request without tools."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Hello! How can I help?",
                        "tool_calls": None,
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        config = ModelConfig()
        client = LLMClient(config)
        messages = [Message(role=Role.USER, content="Hello")]

        content, tool_calls = client.chat(messages)

        assert content == "Hello! How can I help?"
        assert tool_calls is None
        mock_post.assert_called_once()

    @patch.object(httpx.Client, "post")
    def test_chat_success_with_tools(self, mock_post):
        """Test successful chat request with tool calls."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Let me check that.",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "function": {
                                    "name": "read_file",
                                    "arguments": '{"path": "test.txt"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        config = ModelConfig()
        client = LLMClient(config)
        messages = [Message(role=Role.USER, content="Read test.txt")]
        tools = [{"type": "function", "function": {"name": "read_file"}}]

        content, tool_calls = client.chat(messages, tools=tools)

        assert content == "Let me check that."
        assert tool_calls is not None
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "read_file"
        assert tool_calls[0].id == "call_123"

    @patch.object(httpx.Client, "post")
    def test_chat_empty_choices(self, mock_post):
        """Test handling of empty choices in response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        config = ModelConfig()
        client = LLMClient(config)
        messages = [Message(role=Role.USER, content="Hello")]

        content, tool_calls = client.chat(messages)

        assert content == ""
        assert tool_calls is None

    @patch.object(httpx.Client, "post")
    def test_chat_with_retry_on_failure(self, mock_post):
        """Test that chat retries on HTTP errors."""
        # First two calls fail, third succeeds
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Success!", "tool_calls": None}}]
        }
        mock_response.raise_for_status = MagicMock()

        mock_post.side_effect = [
            httpx.HTTPError("Connection error"),
            httpx.HTTPError("Timeout"),
            mock_response,
        ]

        config = ModelConfig(retry_count=3)
        client = LLMClient(config)
        messages = [Message(role=Role.USER, content="Hello")]

        content, tool_calls = client.chat(messages)

        assert content == "Success!"
        assert mock_post.call_count == 3

    @patch.object(httpx.Client, "post")
    def test_chat_raises_error_after_max_retries(self, mock_post):
        """Test that chat raises error after max retries."""
        mock_post.side_effect = httpx.HTTPError("Persistent error")

        config = ModelConfig(retry_count=2)
        client = LLMClient(config)
        messages = [Message(role=Role.USER, content="Hello")]

        with pytest.raises(httpx.HTTPError):
            client.chat(messages)

        # Should have tried retry_count + 1 times
        assert mock_post.call_count == 3


class TestLLMClientChatStream:
    """Tests for LLMClient streaming chat method."""

    @patch.object(httpx.Client, "stream")
    def test_chat_stream_success(self, mock_stream):
        """Test successful streaming chat."""
        # Mock the stream response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines.return_value = [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            'data: {"choices": [{"delta": {"content": " world"}}]}',
            'data: [DONE]',
        ]
        mock_stream.return_value.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.return_value.__exit__ = MagicMock(return_value=False)

        config = ModelConfig()
        client = LLMClient(config)
        messages = [Message(role=Role.USER, content="Hi")]

        chunks = list(client.chat_stream(messages))

        assert chunks == ["Hello", " world"]

    @patch.object(httpx.Client, "stream")
    def test_chat_stream_handles_malformed_json(self, mock_stream):
        """Test that streaming handles malformed JSON gracefully."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines.return_value = [
            'data: not valid json',
            'data: {"choices": [{"delta": {"content": "Valid"}}]}',
            'data: [DONE]',
        ]
        mock_stream.return_value.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.return_value.__exit__ = MagicMock(return_value=False)

        config = ModelConfig()
        client = LLMClient(config)
        messages = [Message(role=Role.USER, content="Hi")]

        chunks = list(client.chat_stream(messages))

        # Should skip malformed JSON and continue
        assert chunks == ["Valid"]


class TestLLMClientBuildPayload:
    """Tests for _build_payload method."""

    def test_build_payload_basic(self):
        """Test building basic payload without tools."""
        config = ModelConfig(model_name="test-model", max_tokens=100)
        client = LLMClient(config)
        messages = [Message(role=Role.USER, content="Hello")]

        payload = client._build_payload(messages, tools=None, stream=False)

        assert payload["model"] == "test-model"
        assert payload["messages"] == [{"role": "user", "content": "Hello"}]
        assert payload["max_tokens"] == 100
        assert payload["stream"] is False
        assert "tools" not in payload

    def test_build_payload_with_tools(self):
        """Test building payload with tools."""
        config = ModelConfig()
        client = LLMClient(config)
        messages = [Message(role=Role.USER, content="Hello")]
        tools = [{"type": "function", "function": {"name": "test"}}]

        payload = client._build_payload(messages, tools=tools, stream=True)

        assert payload["tools"] == tools
        assert payload["stream"] is True

    def test_build_payload_converts_messages_to_dict(self):
        """Test that messages are converted to dict format."""
        config = ModelConfig()
        client = LLMClient(config)
        messages = [
            Message(role=Role.SYSTEM, content="System message"),
            Message(role=Role.USER, content="User message"),
            Message(role=Role.ASSISTANT, content="Assistant message"),
        ]

        payload = client._build_payload(messages, tools=None, stream=False)

        assert len(payload["messages"]) == 3
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][2]["role"] == "assistant"


class TestLLMClientParseResponse:
    """Tests for _parse_response method."""

    def test_parse_response_basic(self):
        """Test parsing basic response."""
        config = ModelConfig()
        client = LLMClient(config)
        response_data = {
            "choices": [
                {"message": {"content": "Test response", "tool_calls": None}}
            ]
        }

        content, tool_calls = client._parse_response(response_data)

        assert content == "Test response"
        assert tool_calls is None

    def test_parse_response_with_tool_calls(self):
        """Test parsing response with tool calls."""
        config = ModelConfig()
        client = LLMClient(config)
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Let me use a tool",
                        "tool_calls": [
                            {
                                "id": "call_abc",
                                "function": {
                                    "name": "write_file",
                                    "arguments": '{"path": "out.txt", "content": "data"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }

        content, tool_calls = client._parse_response(response_data)

        assert content == "Let me use a tool"
        assert tool_calls is not None
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "write_file"
        assert tool_calls[0].id == "call_abc"

    def test_parse_response_empty_content(self):
        """Test parsing response with None content."""
        config = ModelConfig()
        client = LLMClient(config)
        response_data = {
            "choices": [{"message": {"content": None, "tool_calls": None}}]
        }

        content, tool_calls = client._parse_response(response_data)

        assert content == ""
        assert tool_calls is None

    def test_parse_response_no_choices(self):
        """Test parsing response with no choices."""
        config = ModelConfig()
        client = LLMClient(config)
        response_data = {}

        content, tool_calls = client._parse_response(response_data)

        assert content == ""
        assert tool_calls is None

    def test_parse_response_null_tool_calls(self):
        """Test parsing response where tool_calls is explicitly null."""
        config = ModelConfig()
        client = LLMClient(config)
        response_data = {
            "choices": [{"message": {"content": "No tools", "tool_calls": None}}]
        }

        content, tool_calls = client._parse_response(response_data)

        assert content == "No tools"
        assert tool_calls is None

    def test_parse_response_empty_tool_calls_list(self):
        """Test parsing response with empty tool_calls list."""
        config = ModelConfig()
        client = LLMClient(config)
        response_data = {
            "choices": [{"message": {"content": "No tools", "tool_calls": []}}]
        }

        content, tool_calls = client._parse_response(response_data)

        assert content == "No tools"
        assert tool_calls is None
