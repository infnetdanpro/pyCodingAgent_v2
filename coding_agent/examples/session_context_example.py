"""Example: Using session context preparation with the coding agent.

This example demonstrates how to use the new session context preparation
feature that automatically gathers environment information before starting
a session with the LLM.
"""

from coding_agent.core import CodingAgent, prepare_session_context


def example_basic_usage():
    """Basic usage with automatic context preparation (default)."""
    print("=== Example 1: Basic Usage (Default) ===")
    print("Creating agent with prepare_context=True (default)...")
    
    # By default, prepare_context=True, so context is prepared automatically
    agent = CodingAgent()
    
    # The session context is automatically added to the conversation
    ctx = agent.get_context()
    print(f"Session context prepared: {ctx.session_context is not None}")
    
    if ctx.session_context:
        print(f"Context size: {len(ctx.session_context)} characters")
        print("\nFirst 300 chars of context:")
        print(ctx.session_context[:300])
        print("...")
    
    agent.close()


def example_disable_context():
    """Disable context preparation for faster startup."""
    print("\n=== Example 2: Disable Context Preparation ===")
    print("Creating agent with prepare_context=False...")
    
    # Disable context preparation if you don't need it
    agent = CodingAgent(prepare_context=False)
    
    ctx = agent.get_context()
    print(f"Session context prepared: {ctx.session_context is not None}")
    
    agent.close()


def example_manual_context_preparation():
    """Manually prepare context and customize it."""
    print("\n=== Example 3: Manual Context Preparation ===")
    print("Preparing context manually...")
    
    # You can prepare context manually and customize it
    session_ctx = prepare_session_context(
        workspace_dir=".",
        requirements_file="coding_agent/requirements.txt",
    )
    
    print(f"Files found: {len(session_ctx.file_list)}")
    print(f"OS: {session_ctx.os_info.split(chr(10))[0]}")
    print(f"Packages installed: {len(session_ctx.pip_freeze.split(chr(10)))} lines")
    
    # Convert to system prompt format
    context_str = session_ctx.to_system_prompt()
    print(f"\nTotal context size: {len(context_str)} characters")
    
    # You can also access individual components
    print("\nPython coding rules preview:")
    print(session_ctx.python_rules[:200])
    print("...")


def example_with_custom_settings():
    """Use context preparation with custom settings."""
    print("\n=== Example 4: Custom Settings with Context ===")
    
    from coding_agent.config import Settings
    
    # Create custom settings
    settings = Settings(
        workspace_dir=".",
        max_iterations=30,
        enable_history=True,
    )
    
    # Agent will use these settings AND prepare context
    agent = CodingAgent(
        settings=settings,
        prepare_context=True,
    )
    
    ctx = agent.get_context()
    print(f"Max iterations: {settings.max_iterations}")
    print(f"History enabled: {settings.enable_history}")
    print(f"Session context prepared: {ctx.session_context is not None}")
    
    agent.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Session Context Preparation Examples")
    print("=" * 60)
    
    example_basic_usage()
    example_disable_context()
    example_manual_context_preparation()
    example_with_custom_settings()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
