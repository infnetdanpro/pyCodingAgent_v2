#!/usr/bin/env python3
"""CLI entry point for the coding agent."""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

from coding_agent.config import ModelConfig, Settings
from coding_agent.core import CodingAgent, PlanMode, VulnerabilityRemediator, EnhancedPlanner, HierarchicalPlan, PlanStatus
from coding_agent.tools import (
    ListDirTool,
    ReadFileTool,
    RunCommandTool,
    RunPythonTool,
    SearchFilesTool,
    WriteFileTool,
    VulnerabilityScannerTool,
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
    agent.register_tool(VulnerabilityScannerTool(workspace_root=workspace_dir))
    
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
            print("  /help           - Show available commands")
            print("  /clear          - Clear conversation history")
            print("  /retry          - Retry the last task")
            print("  /tools          - List available tools")
            print("  /plan           - Generate a plan for your request")
            print("  /scan           - Scan for vulnerabilities and create remediation plan")
            print("  /quit           - Exit the agent")
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
                        print("  /help           - Show this help message")
                        print("  /clear          - Clear conversation history")
                        print("  /retry          - Retry the last task")
                        print("  /tools          - List available tools")
                        print("  /plan           - Generate and review a plan")
                        print("  /scan           - Scan for vulnerabilities")
                        print("  /quit           - Exit the agent")
                        print("  <text>          - Send a message to the agent\n")
                    
                    elif command == "/clear":
                        agent.clear_context()
                        print("Conversation history cleared.\n")
                    
                    elif command == "/retry":
                        # Retry the last task
                        last_task = agent.retry_last_task()
                        if last_task:
                            print(f"\nRetrying last task: {last_task}\n")
                            try:
                                loader = Loader("Waiting for LLM response...")
                                loader.start()
                                response = agent.run(last_task)
                                loader.stop()
                                print("\n" + response + "\n")
                            except Exception as e:
                                loader.stop()
                                print(f"\nError: {e}\n")
                        else:
                            print("\nNo previous task found to retry.\n")
                    
                    elif command == "/tools":
                        print("\nAvailable tools:")
                        for tool_name in agent.tool_registry.list_tools():
                            print(f"  - {tool_name}")
                        print()
                    
                    elif command == "/plan":
                        # Plan mode workflow with enhanced execution tracking
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
                        
                        # Generate plan using EnhancedPlanner for better tracking
                        planner = EnhancedPlanner(model_config)
                        loader = Loader("Generating plan...")
                        loader.start()
                        hierarchical_plan = planner.generate_hierarchical_plan(
                            plan_request, 
                            system_prompt, 
                            available_tools
                        )
                        loader.stop()
                        
                        if hierarchical_plan:
                            # Display plan summary
                            print("\n" + planner.get_plan_summary(hierarchical_plan))
                            
                            # Convert plan items to format expected by selector
                            plan_items = []
                            for item in hierarchical_plan.get_executable_items():
                                plan_items.append({
                                    'description': item.description,
                                    'tool_name': item.tool_name,
                                    'enabled': True,
                                    'item_id': item.id
                                })
                            
                            # Let user review and modify plan
                            confirmed, enabled_items = interactive_plan_selector(plan_items)
                            
                            if confirmed and enabled_items:
                                print(f"\nExecuting {len(enabled_items)} selected plan items...\n")
                                
                                # Track execution results
                                execution_results = []
                                failed_items = []
                                
                                # Set up callback for progress updates
                                def on_item_status_change(item):
                                    status_icon = "✓" if item.status == PlanStatus.COMPLETED else "✗" if item.status == PlanStatus.FAILED else "○"
                                    print(f"  {status_icon} {item.description[:50]}... ({item.status.value})")
                                
                                planner.set_execution_callback(on_item_status_change)
                                
                                # Create executor function that uses the agent
                                def execute_plan_item(item) -> tuple[bool, str]:
                                    """Execute a single plan item using the agent."""
                                    try:
                                        # Build request for this specific item, including original requirements
                                        item_request = f"""Original task: {plan_request}

Current step to execute: {item.description}"""
                                        if item.tool_name:
                                            item_request += f"\n\nUse the {item.tool_name} tool to complete this step."
                                        
                                        response = agent.run(item_request)
                                        
                                        # Check if response indicates failure
                                        if response.lower().startswith(("error:", "failed:", "i couldn't", "i cannot")):
                                            return False, response
                                        
                                        return True, response
                                    except Exception as e:
                                        return False, str(e)
                                
                                # Execute plan with interactive failure handling
                                loader = Loader("Executing plan...")
                                loader.start()
                                success, message = planner.execute_plan(
                                    hierarchical_plan,
                                    execute_plan_item,
                                    create_checkpoints=True,
                                    interactive_on_failure=True
                                )
                                loader.stop()
                                
                                print(f"\n{'='*60}")
                                if success:
                                    print("✅ Plan executed successfully!")
                                else:
                                    print(f"❌ {message}")
                                
                                # Show final plan status
                                print("\nFinal Status:")
                                print(planner.get_plan_summary(hierarchical_plan))
                                print(f"{'='*60}\n")
                                
                            elif confirmed:
                                print("\nNo items selected for execution.\n")
                            else:
                                print("\nPlan execution cancelled.\n")
                        else:
                            print("Failed to generate plan.\n")
                    
                    elif command == "/scan":
                        # Vulnerability scanning and remediation workflow
                        scan_args = user_input[6:].strip()
                        path = "."
                        file_pattern = "*.py"
                        
                        if scan_args:
                            parts = scan_args.split()
                            if len(parts) >= 1:
                                path = parts[0]
                            if len(parts) >= 2:
                                file_pattern = parts[1]
                        
                        print(f"\n🔍 Scanning for vulnerabilities in {path} (pattern: {file_pattern})...")
                        
                        # Create remediator with agent's model config and tool registry
                        remediator = VulnerabilityRemediator(
                            model_config=model_config,
                            tool_registry=agent.tool_registry
                        )
                        
                        # Step 1: Scan for vulnerabilities
                        loader = Loader("Scanning code...")
                        loader.start()
                        findings = remediator.scan_for_vulnerabilities(path=path, file_pattern=file_pattern)
                        loader.stop()
                        
                        if not findings:
                            print("\n✅ No vulnerabilities detected!\n")
                        else:
                            print(f"\n⚠️  Found {len(findings)} potential vulnerabilities.\n")
                            
                            # Step 2: Generate remediation plan
                            print("Generating remediation plan...")
                            loader = Loader("Creating plan...")
                            loader.start()
                            plan = remediator.generate_remediation_plan()
                            loader.stop()
                            
                            # Step 3: Show plan to user for approval
                            print("\n" + remediator.format_plan_for_display())
                            
                            # Step 4: Interactive loop for plan modification
                            while True:
                                try:
                                    action = input("\nAction (toggle <n>, enable-all, disable-all, approve, cancel): ").strip().lower()
                                except (EOFError, KeyboardInterrupt):
                                    print("\nGoodbye!")
                                    break
                                
                                if action.startswith("toggle"):
                                    try:
                                        index = int(action.split()[1]) - 1
                                        new_status = remediator.toggle_plan_item(index)
                                        status_text = "enabled" if new_status else "disabled"
                                        print(f"Item {index + 1} {status_text}.")
                                        print("\n" + remediator.format_plan_for_display())
                                    except (IndexError, ValueError):
                                        print("Usage: toggle <number>")
                                
                                elif action == "enable-all":
                                    remediator.enable_all_items()
                                    print("All items enabled.")
                                    print("\n" + remediator.format_plan_for_display())
                                
                                elif action == "disable-all":
                                    remediator.disable_all_items()
                                    print("All items disabled.")
                                    print("\n" + remediator.format_plan_for_display())
                                
                                elif action in ("approve", "run"):
                                    # Get enabled items count
                                    enabled_count = sum(1 for item in plan.items if item.enabled)
                                    if enabled_count == 0:
                                        print("\n⚠️  No items enabled. Please enable at least one item or use 'cancel'.")
                                        continue
                                    
                                    print(f"\n🚀 Executing {enabled_count} selected fix(es)...")
                                    
                                    # Apply all enabled fixes
                                    results = remediator.apply_all_enabled_fixes()
                                    
                                    success_count = sum(1 for v in results.values() if v)
                                    fail_count = len(results) - success_count
                                    
                                    print(f"\n✅ Successfully applied {success_count} fix(es).")
                                    if fail_count > 0:
                                        print(f"❌ Failed to apply {fail_count} fix(es).")
                                    
                                    # Verify fixes
                                    print("\nVerifying fixes...")
                                    remaining = remediator.verify_fixes()
                                    if remaining:
                                        print(f"⚠️  {len(remaining)} vulnerability(ies) still remain.")
                                    else:
                                        print("✅ All selected vulnerabilities have been fixed!")
                                    
                                    break
                                
                                elif action == "cancel":
                                    print("\nRemediation cancelled.\n")
                                    break
                                
                                else:
                                    print("Unknown action. Use: toggle <n>, enable-all, disable-all, approve, cancel")
                    
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
