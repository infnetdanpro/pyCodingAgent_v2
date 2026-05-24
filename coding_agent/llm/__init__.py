"""LLM module for OpenAI-compatible model connections."""

from .client import LLMClient
from .message import Message, Role

__all__ = ["LLMClient", "Message", "Role"]
