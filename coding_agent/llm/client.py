"""OpenAI-compatible LLM client for local models."""

import json
import logging
from typing import Any, Generator, Optional

import httpx

from ..config import ModelConfig
from .message import Message, ToolCall

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for OpenAI-compatible LLM APIs.

    Supports local models like Qwen2.5-Coder via Ollama or similar services.

    Attributes:
        config: Model configuration settings.
    """

    def __init__(self, config: ModelConfig) -> None:
        """Initialize the LLM client.

        Args:
            config: Model configuration.
        """
        self.config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "LLMClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        stream: bool = False,
    ) -> tuple[str, Optional[list[ToolCall]]]:
        """Send a chat request to the LLM.

        Args:
            messages: List of conversation messages.
            tools: Optional list of tool schemas.
            stream: Whether to stream the response.

        Returns:
            Tuple of (response content, optional tool calls).
        """
        payload = self._build_payload(messages, tools, stream)

        for attempt in range(self.config.retry_count + 1):
            try:
                response = self._client.post("/chat/completions", json=payload)
                response.raise_for_status()
                return self._parse_response(response.json())
            except httpx.HTTPError as e:
                if attempt == self.config.retry_count:
                    logger.error(f"LLM request failed after {attempt + 1} attempts: {e}")
                    raise
                logger.warning(f"LLM request failed, retrying ({attempt + 1}): {e}")

        raise RuntimeError("Unexpected error in chat request")

    def chat_stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
    ) -> Generator[str, None, None]:
        """Stream a chat response from the LLM.

        Args:
            messages: List of conversation messages.
            tools: Optional list of tool schemas.

        Yields:
            Chunks of response content.
        """
        payload = self._build_payload(messages, tools, stream=True)

        with self._client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    def _build_payload(
        self,
        messages: list[Message],
        tools: Optional[list[dict]],
        stream: bool,
    ) -> dict:
        """Build the API request payload.

        Args:
            messages: Conversation messages.
            tools: Tool schemas.
            stream: Whether to stream.

        Returns:
            Payload dictionary.
        """
        payload: dict = {
            "model": self.config.model_name,
            "messages": [msg.to_dict() for msg in messages],
            "max_tokens": self.config.max_tokens,
            "stream": stream,
        }

        if tools:
            payload["tools"] = tools

        return payload

    def _parse_response(
        self,
        response_data: dict,
    ) -> tuple[str, Optional[list[ToolCall]]]:
        """Parse the API response.

        Args:
            response_data: Raw response data.

        Returns:
            Tuple of (content, tool calls).
        """
        choices = response_data.get("choices", [])
        if not choices:
            return "", None

        message = choices[0].get("message", {})
        content = message.get("content", "") or ""
        tool_calls = None

        if "tool_calls" in message and message["tool_calls"]:
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"],
                )
                for tc in message["tool_calls"]
            ]

        return content, tool_calls
