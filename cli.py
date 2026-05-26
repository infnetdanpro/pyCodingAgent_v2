#!/usr/bin/env python3
"""CLI entry point for the coding agent."""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

from coding_agent.config import ModelConfig, Settings
from coding_agent.core import CodingAgent, PlanMode
from coding_agent.tools import (
    ListDirTool,
    ReadFileTool,
    RunCommandTool,
    RunPythonTool,
    SearchFilesTool,
    WriteFileTool,
)
from coding_agent.utils import setup_logging, interactive_plan_selector


class Loader:
    """Simple loader animation for displaying progress during LLM requests."""
    
    def __init__(self, message: str = "Loading"):
        self.message = message
        self._running = False
    
    def _animate(self):
        """Display the loading animation."""
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        while self._running:
            sys.stdout.write(f"\r{frames[i % len(frames)]} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\r" + " " * (len(self.message) + 2) + "\r")
        sys.stdout.flush()
    
    def start(self):
        """Start the loader animation."""
        self._running = True
        import threading
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the loader animation."""
        self._running = False
        if hasattr(self, '_thread'):
            self._thread.join(timeout=0.5)


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
            plan_mode = PlanMode(model_config)
            
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
            print("  /plan     - Generate a plan for your request")
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
                        print("  /plan     - Generate and review a plan")
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
                    
                    elif command == "/plan":
                        # Plan mode workflow
                        plan_request = user_input[6:].strip()
                        if not plan_request:
                            print("Usage: /plan <your request>")
                            print("Example: /plan Create a Python script that lists all files in the current directory\n")
                            continue
                        
                        print("\nGenerating plan...")
                        
                        # Get system prompt and available tools
                        context = agent.get_context()
                        system_prompt = context.system_prompt or "You are a helpful coding assistant."
                        available_tools = agent.tool_registry.get_all_schemas()
                        
                        # Generate plan
                        loader = Loader("Generating plan...")
                        loader.start()
                        plan = plan_mode.generate_plan(plan_request, system_prompt, available_tools)
                        loader.stop()
                        
                        if plan:
                            print(f"\n{plan}")
                            
                            # Convert plan items to format expected by selector
                            plan_items = []
                            for item in plan.items:
                                plan_items.append({
                                    'description': item.description,
                                    'tool_name': item.tool_name,
                                    'enabled': True
                                })
                            
                            # Let user review and modify plan
                            confirmed, enabled_items = interactive_plan_selector(plan_items)
                            
                            if confirmed and enabled_items:
                                print(f"\nExecuting {len(enabled_items)} selected plan items...\n")
                                
                                # Build execution request from enabled items
                                execution_request = f"Execute the following plan steps:\n\n"
                                for i, item in enumerate(enabled_items, 1):
                                    execution_request += f"{i}. {item['description']}"
                                    if item.get('tool_name'):
                                        execution_request += f" [using {item['tool_name']}]"
                                    execution_request += "\n"
                                
                                execution_request += "\nPlease execute these steps in order."
                                
                                try:
                                    # Show loader while waiting for LLM response
                                    loader = Loader("Executing plan...")
                                    loader.start()
                                    response = agent.run(execution_request)
                                    loader.stop()
                                    print("\n" + response + "\n")
                                except Exception as e:
                                    loader.stop()
                                    print(f"\nError during execution: {e}\n")
                            elif confirmed:
                                print("\nNo items selected for execution.\n")
                            else:
                                print("\nPlan execution cancelled.\n")
                        else:
                            print("Failed to generate plan.\n")
                    
                    else:
                        print(f"Unknown command: {command}. Type /help for available commands.\n")
                    continue
                
                if not user_input:
                    continue
                
                try:
                    # Show loader while waiting for LLM response
                    loader = Loader("Waiting for LLM response...")
                    loader.start()
                    response = agent.run(user_input)
                    loader.stop()
                    print("\n" + response + "\n")
                except Exception as e:
                    loader.stop()
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
