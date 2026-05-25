"""OpenAI-compatible LLM client for local models."""

import json
import logging
import re
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

        # First check for native tool_calls format (OpenAI standard)
        if "tool_calls" in message and message["tool_calls"]:
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"],
                )
                for tc in message["tool_calls"]
            ]
        # Fallback: Parse tool calls from content for models that don't support native tool calling
        # This handles cases where the model outputs JSON tool calls in markdown code blocks
        elif content:
            parsed_tool_calls = self._parse_tool_calls_from_content(content)
            if parsed_tool_calls:
                tool_calls = parsed_tool_calls

        return content, tool_calls

    def _parse_tool_calls_from_content(self, content: str) -> Optional[list[ToolCall]]:
        """Parse tool calls from message content.

        Some models (like smaller Qwen variants) may output tool calls as JSON
        in their content instead of using the native tool_calls format.

        Args:
            content: Message content that may contain tool call JSON.

        Returns:
            List of ToolCall objects if found, None otherwise.
        """
        # First try to extract JSON from markdown code blocks
        code_block_pattern = r'```(?:\s*json)?\s*(\{.*?\})\s*```'
        matches = re.findall(code_block_pattern, content, re.DOTALL)
        
        # If no code blocks found, try to find standalone JSON objects with name/arguments
        if not matches:
            # Look for JSON-like structures that contain both "name" and "arguments"
            # Use non-greedy .* to match nested braces properly
            json_pattern = r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:.*\}'
            matches = re.findall(json_pattern, content, re.DOTALL)
        
        if not matches:
            return None
        
        tool_calls = []
        for i, match in enumerate(matches):
            try:
                data = json.loads(match.strip())
                if "name" in data and "arguments" in data:
                    # Generate a unique ID for each tool call
                    tool_call_id = f"call_{i}_{data['name']}"
                    
                    # Arguments might already be a dict or might need parsing
                    arguments = data["arguments"]
                    if isinstance(arguments, dict):
                        arguments = json.dumps(arguments)
                    
                    tool_calls.append(
                        ToolCall(
                            id=tool_call_id,
                            name=data["name"],
                            arguments=arguments,
                        )
                    )
            except json.JSONDecodeError:
                continue
        
        return tool_calls if tool_calls else None
