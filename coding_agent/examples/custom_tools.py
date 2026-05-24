"""Example: Custom tool creation and registration."""

from typing import Any

from coding_agent.config import ModelConfig, Settings
from coding_agent.core import CodingAgent
from coding_agent.tools import Tool, ToolResult
from coding_agent.utils import setup_logging


class GetCurrentTimeTool(Tool):
    """Example custom tool that returns the current time."""

    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return "Get the current date and time. Useful for timestamping or scheduling tasks."

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Optional datetime format string (default: ISO format)",
                },
            },
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        from datetime import datetime

        try:
            fmt = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now().strftime(fmt)
            return ToolResult(success=True, output=current_time)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CalculateTool(Tool):
    """Example custom tool for mathematical calculations."""

    @property
    def name(self) -> str:
        return "calculate"

    @property
    def description(self) -> str:
        return "Perform a mathematical calculation. Supports basic arithmetic operations."

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')",
                },
            },
            "required": ["expression"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            expression = kwargs.get("expression", "")
            if not expression:
                return ToolResult(success=False, error="Missing expression parameter")

            # Safe evaluation using eval with restricted builtins
            allowed_names = {"__builtins__": {}}
            result = eval(expression, allowed_names, {})
            return ToolResult(success=True, output=str(result))

        except Exception as e:
            return ToolResult(success=False, error=f"Calculation error: {e}")


def main() -> None:
    """Demonstrate custom tool usage."""
    setup_logging(level="INFO")

    settings = Settings(workspace_dir=".")
    model_config = ModelConfig(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model_name="qwen2.5-coder:7b",
    )

    with CodingAgent(settings=settings, model_config=model_config) as agent:
        # Register custom tools
        agent.register_tool(GetCurrentTimeTool())
        agent.register_tool(CalculateTool())

        print("Custom Tools Example")
        print("=" * 60)
        print("\nRegistered custom tools:")
        for tool_name in agent.tool_registry.list_tools():
            tool = agent.tool_registry.get(tool_name)
            print(f"\n  {tool.name}:")
            print(f"    Description: {tool.description}")

        # Test the tools directly
        print("\n" + "=" * 60)
        print("Testing tools directly:\n")

        # Test time tool
        time_result = agent.tool_registry.execute("get_current_time")
        print(f"Current time: {time_result.output}")

        # Test calculate tool
        calc_result = agent.tool_registry.execute("calculate", expression="2 + 3 * 4")
        print(f"2 + 3 * 4 = {calc_result.output}")


if __name__ == "__main__":
    main()
