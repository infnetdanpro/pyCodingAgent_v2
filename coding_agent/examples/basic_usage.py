"""Example usage of the coding agent."""

from coding_agent.config import ModelConfig, Settings
from coding_agent.core import CodingAgent
from coding_agent.tools import (
    ListDirTool,
    ReadFileTool,
    RunCommandTool,
    RunPythonTool,
    SearchFilesTool,
    WriteFileTool,
)
from coding_agent.utils import setup_logging


def main() -> None:
    """Run the coding agent example."""
    # Setup logging
    setup_logging(level="INFO")

    # Configure settings
    settings = Settings(
        workspace_dir=".",
        max_iterations=50,
        log_level="INFO",
    )

    # Configure model (adjust for your local setup or use environment variables)
    model_config = ModelConfig(
        base_url="http://localhost:11434/v1",  # Ollama default, or set LLM_BASE_URL env var
        api_key="ollama",  # Dummy key for local models, or set LLM_API_KEY env var
        model_name="qwen2.5-coder:7b",  # Or set LLM_MODEL env var
    )

    # Create agent with context manager for proper cleanup
    with CodingAgent(settings=settings, model_config=model_config) as agent:
        # Register available tools
        agent.register_tool(ReadFileTool(workspace_root=settings.workspace_dir))
        agent.register_tool(WriteFileTool(workspace_root=settings.workspace_dir))
        agent.register_tool(ListDirTool(workspace_root=settings.workspace_dir))
        agent.register_tool(SearchFilesTool(workspace_root=settings.workspace_dir))
        agent.register_tool(RunCommandTool(workspace_root=settings.workspace_dir))
        agent.register_tool(RunPythonTool(workspace_root=settings.workspace_dir))

        # Example interaction
        print("=" * 60)
        print("Coding Agent Ready!")
        print("=" * 60)
        print("\nAvailable tools:")
        for tool_name in agent.tool_registry.list_tools():
            print(f"  - {tool_name}")
        print("\nEnter your request (or 'quit' to exit):\n")

        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            if not user_input:
                continue

            try:
                response = agent.run(user_input)
                print("\n" + response + "\n")
            except Exception as e:
                print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
