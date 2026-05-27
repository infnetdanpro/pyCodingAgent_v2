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

        logger.info(f"Sending chat request to LLM (model: {self.config.model_name})")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)[:500]}...")

        for attempt in range(self.config.retry_count + 1):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.config.retry_count + 1}")
                response = self._client.post("/chat/completions", json=payload)
                response.raise_for_status()
                result = self._parse_response(response.json())
                logger.info(f"LLM response received successfully")
                logger.debug(f"Response content length: {len(result[0])}, tool_calls: {len(result[1]) if result[1] else 0}")
                return result
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

        logger.info(f"Starting streaming chat request to LLM (model: {self.config.model_name})")
        
        with self._client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            logger.debug("Streaming connection established")
            
            chunk_count = 0
            total_content_length = 0
            
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        logger.debug("Received [DONE] signal")
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            chunk_count += 1
                            total_content_length += len(content)
                            yield content
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"Streaming complete: received {chunk_count} chunks, {total_content_length} characters")

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
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
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
        logger.debug(f"Parsing LLM response")
        
        choices = response_data.get("choices", [])
        if not choices:
            logger.warning("No choices in LLM response")
            return "", None

        message = choices[0].get("message", {})
        content = message.get("content", "") or ""
        tool_calls = None

        # First check for native tool_calls format (OpenAI standard)
        if "tool_calls" in message and message["tool_calls"]:
            logger.info(f"Found {len(message['tool_calls'])} native tool calls in response")
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
                logger.info(f"Parsed {len(parsed_tool_calls)} tool calls from content")
                tool_calls = parsed_tool_calls

        logger.debug(f"Response content length: {len(content)}, tool_calls found: {len(tool_calls) if tool_calls else 0}")
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
        # Preprocess content to handle common issues from model output
        content = self._preprocess_json_content(content)
        
        # Try multiple patterns to extract JSON tool calls from various formats
        
        # Pattern 1: JSON in markdown code blocks (with optional language tag like json, result, etc.)
        # Handles: ```json {...} ``` or ```result {...} ``` or just ``` {...} ```
        code_block_pattern = r'```\s*(?:\w+)?\s*(\{.*?"name"\s*:\s*".*?"\s*,\s*"arguments".*?\})\s*```'
        matches = re.findall(code_block_pattern, content, re.DOTALL)
        
        # Pattern 2: Standalone JSON objects with name/arguments fields
        # Use balanced brace matching for nested objects
        if not matches:
            json_pattern = r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}'
            matches = re.findall(json_pattern, content, re.DOTALL)
        
        # Pattern 3: More flexible JSON extraction - find all { } blocks and filter
        if not matches:
            # Find potential JSON blocks by looking for opening braces
            brace_start = -1
            brace_count = 0
            potential_matches = []
            
            for i, char in enumerate(content):
                if char == '{':
                    if brace_count == 0:
                        brace_start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and brace_start != -1:
                        potential_json = content[brace_start:i+1]
                        potential_matches.append(potential_json)
                        brace_start = -1
            
            # Filter to only those that look like tool calls
            for candidate in potential_matches:
                if '"name"' in candidate and '"arguments"' in candidate:
                    matches.append(candidate)
        
        if not matches:
            return None
        
        tool_calls = []
        for i, match in enumerate(matches):
            try:
                # Pre-process the JSON string to handle common issues
                cleaned = match.strip()
                
                data = json.loads(cleaned)
                
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
    
    def _preprocess_json_content(self, content: str) -> str:
        """Preprocess content to fix common JSON formatting issues from model output.
        
        Models sometimes output invalid JSON with:
        - Python-style triple quotes for multi-line strings
        - Unescaped newlines inside string values
        
        Args:
            content: Raw content that may contain malformed JSON.
            
        Returns:
            Content with fixed JSON formatting.
        """
        # Replace triple double quotes with single double quotes
        content = content.replace('"""', '"')
        
        # Replace triple single quotes with single double quotes  
        content = content.replace("'''", '"')
        
        # Escape unescaped newlines/tabs/carriage returns inside string values
        # This is a character-by-character approach to track when we're inside a string
        result = []
        in_string = False
        i = 0
        while i < len(content):
            char = content[i]
            
            # Toggle string state when encountering unescaped quote
            if char == '"' and (i == 0 or content[i-1] != '\\'):
                in_string = not in_string
                result.append(char)
            elif in_string and char == '\n':
                # Escape newline inside string
                result.append('\\n')
            elif in_string and char == '\r':
                # Escape carriage return inside string  
                result.append('\\r')
            elif in_string and char == '\t':
                # Escape tab inside string
                result.append('\\t')
            else:
                result.append(char)
            i += 1
        
        return ''.join(result)
