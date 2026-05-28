"""Shell command execution tools for the coding agent."""

import subprocess
from typing import Any

from .base import Tool, ToolResult


class ShellTools:
    """Collection of shell command execution tools.

    Provides safe command execution with timeout and output capture.
    """

    def __init__(self, workspace_root: str = ".", timeout: int = 300) -> None:
        """Initialize shell tools.

        Args:
            workspace_root: Working directory for commands.
            timeout: Default timeout for command execution in seconds.
        """
        self.workspace_root = workspace_root
        self.timeout = timeout


class RunCommandTool(Tool):
    """Tool for executing shell commands."""

    def __init__(self, workspace_root: str = ".", timeout: int = 300) -> None:
        """Initialize the run command tool.

        Args:
            workspace_root: Working directory for commands.
            timeout: Timeout for command execution in seconds.
        """
        self._shell_tools = ShellTools(workspace_root, timeout)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "run_command"

    @property
    def description(self) -> str:
        """Return tool description."""
        return (
            "Execute a shell command in the workspace directory. "
            "Use for running tests, building projects, or system operations. "
            "Commands are executed safely without shell injection vulnerabilities."
        )

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (optional, uses default if not specified)",
                },
            },
            "required": ["command"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the shell command.

        Args:
            **kwargs: Must contain 'command' key, optionally 'timeout'.

        Returns:
            ToolResult with command output or error.
        """
        try:
            command = kwargs.get("command")
            timeout = kwargs.get("timeout", self._shell_tools.timeout)

            if not command:
                return ToolResult(success=False, error="Missing required parameter: command")

            # Execute command in a shell to support shell features like cd, &&, ||, etc.
            result = subprocess.run(
                command,
                shell=True,
                cwd=self._shell_tools.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(f"STDERR:\n{result.stderr}")

            output = "\n".join(output_parts) if output_parts else "(no output)"

            success = result.returncode == 0
            return ToolResult(
                success=success,
                output=output,
                error=None if success else f"Command exited with code {result.returncode}",
            )

        except subprocess.TimeoutExpired as e:
            return ToolResult(success=False, error=f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class RunPythonTool(Tool):
    """Tool for executing Python code snippets."""

    def __init__(self, workspace_root: str = ".", timeout: int = 60) -> None:
        """Initialize the run Python tool.

        Args:
            workspace_root: Working directory for execution.
            timeout: Timeout for code execution in seconds.
        """
        self._shell_tools = ShellTools(workspace_root, timeout)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "run_python"

    @property
    def description(self) -> str:
        """Return tool description."""
        return (
            "Execute a Python code snippet. Useful for quick calculations, "
            "data processing, or testing small pieces of code."
        )

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
            },
            "required": ["code"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the Python code.

        Args:
            **kwargs: Must contain 'code' key.

        Returns:
            ToolResult with execution output or error.
        """
        try:
            code = kwargs.get("code")

            if not code:
                return ToolResult(success=False, error="Missing required parameter: code")

            # Execute Python directly without shell for security
            result = subprocess.run(
                ["python3", "-c", code],
                shell=False,
                cwd=self._shell_tools.workspace_root,
                capture_output=True,
                text=True,
                timeout=self._shell_tools.timeout,
            )

            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(f"STDERR:\n{result.stderr}")

            output = "\n".join(output_parts) if output_parts else "(no output)"

            success = result.returncode == 0
            return ToolResult(
                success=success,
                output=output,
                error=None if success else f"Python execution failed with code {result.returncode}",
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False, error=f"Python code timed out after {self._shell_tools.timeout}s"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
