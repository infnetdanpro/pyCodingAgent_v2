#!/usr/bin/env python3
"""CLI entry point for the coding agent."""

import argparse
import os
import sys
from pathlib import Path

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


def create_agent(workspace_dir: str, model_config: ModelConfig) -> CodingAgent:
    """Create and configure a coding agent instance.
    
    Args:
        workspace_dir: Root directory for file operations.
        model_config: LLM model configuration.
    
    Returns:
        Configured CodingAgent instance.
    """
    settings = Settings(
        workspace_dir=workspace_dir,
        max_iterations=50,
        log_level="INFO",
    )
    
    agent = CodingAgent(settings=settings, model_config=model_config)
    
    # Register default tools
    agent.register_tool(ReadFileTool(workspace_root=workspace_dir))
    agent.register_tool(WriteFileTool(workspace_root=workspace_dir))
    agent.register_tool(ListDirTool(workspace_root=workspace_dir))
    agent.register_tool(SearchFilesTool(workspace_root=workspace_dir))
    agent.register_tool(RunCommandTool(workspace_root=workspace_dir))
    agent.register_tool(RunPythonTool(workspace_root=workspace_dir))
    
    return agent


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a directory for use with the coding agent.
    
    Args:
        args: Parsed command-line arguments.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    target_dir = Path(args.directory).resolve()
    
    if not target_dir.exists():
        print(f"Creating directory: {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .agent_config.json if it doesn't exist
    config_file = target_dir / ".agent_config.json"
    if not config_file.exists():
        import json
        config_content = {
            "workspace_dir": str(target_dir),
            "model": {
                "base_url": os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
                "api_key": os.getenv("LLM_API_KEY", "ollama"),
                "model_name": os.getenv("LLM_MODEL", "qwen2.5-coder:7b")
            }
        }
        with open(config_file, 'w') as f:
            json.dump(config_content, f, indent=2)
        print(f"Created configuration file: {config_file}")
    else:
        print(f"Configuration already exists: {config_file}")
    
    # Create .gitignore for agent history
    gitignore_file = target_dir / ".gitignore"
    if not gitignore_file.exists():
        with open(gitignore_file, 'w') as f:
            f.write(".agent_history/\n")
            f.write("__pycache__/\n")
            f.write("*.pyc\n")
        print(f"Created .gitignore: {gitignore_file}")
    
    # Create virtualenv recommendation
    venv_dir = target_dir / "venv"
    if not venv_dir.exists():
        print(f"\nTo create a virtual environment, run:")
        print(f"  cd {target_dir}")
        print(f"  python -m venv venv")
        print(f"  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print(f"  pip install -e .  # If you have setup.py or pyproject.toml")
    
    print(f"\nDirectory initialized: {target_dir}")
    print("You can now use 'agent chat' to start interacting with the coding agent.")
    
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    """Start an interactive chat session with the coding agent.
    
    Args:
        args: Parsed command-line arguments.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    workspace_dir = Path(args.workspace).resolve()
    
    if not workspace_dir.exists():
        print(f"Error: Workspace directory does not exist: {workspace_dir}")
        return 1
    
    # Load model configuration
    model_config = ModelConfig(
        base_url=args.base_url,
        api_key=args.api_key,
        model_name=args.model,
    )
    
    setup_logging(level=args.log_level)
    
    try:
        with create_agent(str(workspace_dir), model_config) as agent:
            print("=" * 60)
            print("Coding Agent CLI")
            print("=" * 60)
            print(f"Workspace: {workspace_dir}")
            print(f"Model: {args.model}")
            print(f"Base URL: {args.base_url}")
            print("=" * 60)
            print("\nCommands:")
            print("  /help     - Show available commands")
            print("  /clear    - Clear conversation history")
            print("  /tools    - List available tools")
            print("  /quit     - Exit the agent")
            print("\nEnter your request:\n")
            
            while True:
                try:
                    user_input = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break
                
                if user_input.lower() in ("/quit", "/exit", "quit", "exit", "q"):
                    print("Goodbye!")
                    break
                
                if user_input.startswith("/"):
                    command = user_input.split()[0].lower()
                    
                    if command == "/help":
                        print("\nAvailable commands:")
                        print("  /help     - Show this help message")
                        print("  /clear    - Clear conversation history")
                        print("  /tools    - List available tools")
                        print("  /quit     - Exit the agent")
                        print("  <text>    - Send a message to the agent\n")
                    
                    elif command == "/clear":
                        agent.clear_context()
                        print("Conversation history cleared.\n")
                    
                    elif command == "/tools":
                        print("\nAvailable tools:")
                        for tool_name in agent.tool_registry.list_tools():
                            print(f"  - {tool_name}")
                        print()
                    
                    else:
                        print(f"Unknown command: {command}. Type /help for available commands.\n")
                    continue
                
                if not user_input:
                    continue
                
                try:
                    response = agent.run(user_input)
                    print("\n" + response + "\n")
                except Exception as e:
                    print(f"\nError: {e}\n")
    
    except Exception as e:
        print(f"Error initializing agent: {e}")
        return 1
    
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run a single command with the coding agent.
    
    Args:
        args: Parsed command-line arguments.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    workspace_dir = Path(args.workspace).resolve()
    
    if not workspace_dir.exists():
        print(f"Error: Workspace directory does not exist: {workspace_dir}")
        return 1
    
    # Load model configuration
    model_config = ModelConfig(
        base_url=args.base_url,
        api_key=args.api_key,
        model_name=args.model,
    )
    
    setup_logging(level=args.log_level)
    
    try:
        with create_agent(str(workspace_dir), model_config) as agent:
            response = agent.run(args.command)
            print(response)
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        prog="agent",
        description="Coding Agent CLI - AI-powered coding assistant",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a directory for use with the coding agent",
    )
    init_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to initialize (default: current directory)",
    )
    init_parser.set_defaults(func=cmd_init)
    
    # Chat command
    chat_parser = subparsers.add_parser(
        "chat",
        help="Start an interactive chat session with the coding agent",
    )
    chat_parser.add_argument(
        "-w", "--workspace",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    chat_parser.add_argument(
        "--base-url",
        default=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        help="LLM API base URL (default: http://localhost:11434/v1)",
    )
    chat_parser.add_argument(
        "--api-key",
        default=os.getenv("LLM_API_KEY", "ollama"),
        help="LLM API key (default: ollama)",
    )
    chat_parser.add_argument(
        "--model",
        default=os.getenv("LLM_MODEL", "qwen2.5-coder:7b"),
        help="LLM model name (default: from .env or qwen2.5-coder:7b)",
    )
    chat_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    chat_parser.set_defaults(func=cmd_chat)
    
    # Run command
    run_parser = subparsers.add_parser(
        "run",
        help="Run a single command with the coding agent",
    )
    run_parser.add_argument(
        "command",
        help="Command to execute",
    )
    run_parser.add_argument(
        "-w", "--workspace",
        default=".",
        help="Workspace directory (default: current directory)",
    )
    run_parser.add_argument(
        "--base-url",
        default=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        help="LLM API base URL (default: http://localhost:11434/v1)",
    )
    run_parser.add_argument(
        "--api-key",
        default=os.getenv("LLM_API_KEY", "ollama"),
        help="LLM API key (default: ollama)",
    )
    run_parser.add_argument(
        "--model",
        default=os.getenv("LLM_MODEL", "qwen2.5-coder:7b"),
        help="LLM model name (default: from .env or qwen2.5-coder:7b)",
    )
    run_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    run_parser.set_defaults(func=cmd_run)
    
    args = parser.parse_args()
    
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
