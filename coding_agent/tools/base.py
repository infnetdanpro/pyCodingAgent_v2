"""Base tool definitions for the coding agent."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolResult:
    """Result of a tool execution.

    Attributes:
        success: Whether the tool executed successfully.
        output: The output from the tool.
        error: Optional error message if execution failed.
    """

    success: bool
    output: str = ""
    error: str | None = None

    def __str__(self) -> str:
        """String representation of the result."""
        if self.success:
            return self.output
        return f"Error: {self.error}"


class Tool(ABC):
    """Abstract base class for all tools.

    Tools are modular components that extend agent capabilities.
    Each tool should have a clear, single responsibility (KISS).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what the tool does."""
        pass

    @property
    @abstractmethod
    def schema(self) -> dict:
        """Return the JSON schema for tool parameters."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            ToolResult with execution outcome.
        """
        pass

    def to_dict(self) -> dict:
        """Convert tool to dictionary format for LLM consumption.

        Returns:
            Dictionary representation compatible with OpenAI API.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema,
            },
        }


class ToolRegistry:
    """Registry for managing available tools.

    Provides centralized tool management following DRY principle.
    """

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry.

        Args:
            tool: Tool instance to register.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool by name.

        Args:
            name: Name of the tool to unregister.

        Raises:
            KeyError: If the tool is not found.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
        del self._tools[name]

    def get(self, name: str) -> Tool:
        """Get a tool by name.

        Args:
            name: Name of the tool.

        Returns:
            The requested tool.

        Raises:
            KeyError: If the tool is not found.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names.
        """
        return list(self._tools.keys())

    def get_all_schemas(self) -> list[dict]:
        """Get schemas for all registered tools.

        Returns:
            List of tool schemas.
        """
        return [tool.to_dict() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name.

        Args:
            name: Name of the tool to execute.
            **kwargs: Tool-specific parameters.

        Returns:
            ToolResult from execution.

        Raises:
            KeyError: If the tool is not found.
        """
        tool = self.get(name)
        return tool.execute(**kwargs)
