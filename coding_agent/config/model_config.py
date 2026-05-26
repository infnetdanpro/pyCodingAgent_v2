"""Model configuration for LLM connections."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """Configuration for LLM model connections.

    Supports OpenAI-compatible APIs including local models like Qwen2.5-Coder.

    Attributes:
        base_url: Base URL for the OpenAI-compatible API endpoint.
        api_key: API key for authentication (can be dummy for local models).
        model_name: Name of the model to use (e.g., 'qwen2.5-coder:7b').
        max_tokens: Maximum tokens in response.
        timeout: Request timeout in seconds.
        retry_count: Number of retries on failure.
    """

    base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"))
    api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", "ollama"))
    model_name: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "qwen2.5-coder:7b"))
    max_tokens: int = 8128
    timeout: int = 120
    retry_count: int = 3
    stream: bool = True

    def __post_init__(self) -> None:
        """Validate model configuration."""
        if not self.base_url:
            raise ValueError("base_url cannot be empty")

        if not self.model_name:
            raise ValueError("model_name cannot be empty")

        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        if self.retry_count < 0:
            raise ValueError("retry_count cannot be negative")
