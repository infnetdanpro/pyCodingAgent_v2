"""Main coding agent implementation."""

import json
import logging
from typing import Optional

from ..config import ModelConfig, Settings
from ..llm import LLMClient, Message, Role
from ..llm.message import ToolCall
from ..tools import ToolRegistry, ToolResult
from .context import ConversationContext

logger = logging.getLogger(__name__)


class CodingAgent:
    """Main coding agent that orchestrates LLM interactions and tool execution.

    The agent follows a ReAct (Reasoning + Acting) pattern:
    1. Receive user input
    2. Query LLM for response/tool calls
    3. Execute tools if requested
    4. Feed results back to LLM
    5. Repeat until completion

    Attributes:
        settings: Agent configuration settings.
        model_config: LLM model configuration.
        tool_registry: Registry of available tools.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        model_config: Optional[ModelConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        """Initialize the coding agent.

        Args:
            settings: Agent settings. Uses defaults if not provided.
            model_config: LLM configuration. Uses defaults if not provided.
            tool_registry: Tool registry. Creates empty registry if not provided.
        """
        self.settings = settings or Settings()
        self.model_config = model_config or ModelConfig()
        self.tool_registry = tool_registry or ToolRegistry()

        self._client = LLMClient(self.model_config)
        self._context = ConversationContext(
            max_length=self.settings.max_iterations,
            system_prompt=self._get_default_system_prompt(),
        )

        if self.settings.enable_history:
            history_path = Path(self.settings.workspace_dir) / self.settings.history_dir
            self._context.history_file = history_path / "conversation.json"

    def _get_default_system_prompt(self) -> str:
        """Generate the default system prompt for the agent.

        Returns:
            System prompt string.
        """
        return """You are an expert coding assistant. You help users with software development tasks.

Guidelines:
- Think step by step before taking action
- Use available tools to accomplish tasks
- Always verify your work when possible
- Write clean, well-documented code
- Follow best practices and design patterns
- If unsure, ask clarifying questions
- Prefer reading existing files before modifying them
- Test changes when appropriate

Available tools allow you to:
- Read and write files
- List directory contents
- Search for files
- Execute shell commands
- Run Python code snippets

Always explain what you're doing and why."""

    def run(self, user_input: str, stream: bool = False) -> str:
        """Process a user request and return the agent's response.

        Args:
            user_input: The user's request or question.
            stream: Whether to stream the response (not yet implemented).

        Returns:
            The agent's final response.
        """
        self._context.add_user_message(user_input)
        logger.info(f"Processing user request: {user_input[:50]}...")

        iteration = 0
        while iteration < self.settings.max_iterations:
            iteration += 1
            logger.debug(f"Iteration {iteration}/{self.settings.max_iterations}")

            messages = self._context.get_messages()
            tools_schema = self.tool_registry.get_all_schemas()

            try:
                content, tool_calls = self._client.chat(messages, tools=tools_schema)
            except Exception as e:
                logger.error(f"LLM request failed: {e}")
                return f"Error: Failed to communicate with LLM - {e}"

            if content:
                self._context.add_assistant_message(content)

            if not tool_calls:
                # No tool calls, we're done
                self._context._save_history()
                return content

            # Execute tool calls
            for tool_call in tool_calls:
                result = self._execute_tool_call(tool_call)
                self._context.add_tool_result(tool_call.id, result.output)

                if not result.success:
                    logger.warning(f"Tool execution failed: {result.error}")

        logger.warning("Max iterations reached")
        return "I've reached the maximum number of iterations. Let me summarize what I've accomplished..."

    def _execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """Execute a single tool call from the LLM.

        Args:
            tool_call: The tool call to execute.

        Returns:
            Result of the tool execution.
        """
        try:
            arguments = json.loads(tool_call.arguments) if tool_call.arguments else {}
        except json.JSONDecodeError:
            return ToolResult(success=False, error="Invalid JSON arguments")

        logger.info(f"Executing tool: {tool_call.name} with args: {arguments}")

        try:
            return self.tool_registry.execute(tool_call.name, **arguments)
        except KeyError:
            return ToolResult(success=False, error=f"Unknown tool: {tool_call.name}")
        except Exception as e:
            return ToolResult(success=False, error=f"Tool execution error: {e}")

    def register_tool(self, tool) -> None:
        """Register a tool with the agent.

        Args:
            tool: Tool instance to register.
        """
        self.tool_registry.register(tool)
        logger.info(f"Registered tool: {tool.name}")

    def get_context(self) -> ConversationContext:
        """Get the current conversation context.

        Returns:
            The conversation context.
        """
        return self._context

    def clear_context(self) -> None:
        """Clear the conversation history."""
        self._context.clear()
        logger.info("Cleared conversation context")

    def close(self) -> None:
        """Close the agent and release resources."""
        self._client.close()
        logger.info("Agent closed")

    def __enter__(self) -> "CodingAgent":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


# Import Path here to avoid circular imports
from pathlib import Path
