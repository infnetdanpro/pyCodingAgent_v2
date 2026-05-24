"""Tests for the shell tools."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from coding_agent.tools.shell import RunCommandTool, RunPythonTool


class TestRunCommandTool:
    """Tests for the RunCommandTool class."""

    def test_run_simple_command(self):
        """Test running a simple shell command."""
        tool = RunCommandTool()
        result = tool.execute(command="echo 'Hello World'")

        assert result.success is True
        assert "Hello World" in result.output

    def test_run_command_with_error(self):
        """Test running a command that fails."""
        tool = RunCommandTool()
        result = tool.execute(command="exit 1")

        assert result.success is False
        assert "exited with code" in result.error.lower()

    def test_run_command_missing_parameter(self):
        """Test that missing command parameter returns error."""
        tool = RunCommandTool()
        result = tool.execute()

        assert result.success is False
        assert "command" in result.error.lower()

    def test_run_command_with_stderr(self):
        """Test running a command that produces stderr output."""
        tool = RunCommandTool()
        result = tool.execute(command="python3 -c \"import sys; print('stdout'); print('stderr', file=sys.stderr)\"")

        assert result.success is True
        assert "stdout" in result.output
        assert "stderr" in result.output

    def test_run_command_no_output(self):
        """Test running a command with no output."""
        tool = RunCommandTool()
        result = tool.execute(command="true")

        assert result.success is True
        assert "no output" in result.output.lower()

    def test_run_command_timeout(self):
        """Test that long-running commands timeout."""
        tool = RunCommandTool(timeout=1)
        # Use sleep command to trigger timeout
        result = tool.execute(command="sleep 5", timeout=1)

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_run_command_with_custom_workspace(self, tmp_path):
        """Test running a command with custom workspace directory."""
        tool = RunCommandTool(workspace_root=str(tmp_path))
        # Create a file in the workspace
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Run pwd command to verify working directory
        result = tool.execute(command="pwd")

        assert result.success is True
        assert str(tmp_path) in result.output


class TestRunPythonTool:
    """Tests for the RunPythonTool class."""

    def test_run_simple_python_code(self):
        """Test running simple Python code."""
        tool = RunPythonTool()
        result = tool.execute(code="print('Hello from Python')")

        assert result.success is True
        assert "Hello from Python" in result.output

    def test_run_python_with_calculation(self):
        """Test running Python code with calculation."""
        tool = RunPythonTool()
        result = tool.execute(code="print(2 + 2)")

        assert result.success is True
        assert "4" in result.output

    def test_run_python_with_error(self):
        """Test running Python code that raises an error."""
        tool = RunPythonTool()
        result = tool.execute(code="raise ValueError('Test error')")

        assert result.success is False
        assert "ValueError" in result.output or "error" in result.error.lower()

    def test_run_python_missing_parameter(self):
        """Test that missing code parameter returns error."""
        tool = RunPythonTool()
        result = tool.execute()

        assert result.success is False
        assert "code" in result.error.lower()

    def test_run_python_no_output(self):
        """Test running Python code with no output."""
        tool = RunPythonTool()
        result = tool.execute(code="pass")

        assert result.success is True
        assert "no output" in result.output.lower()

    def test_run_python_with_multiline_code(self):
        """Test running multiline Python code."""
        tool = RunPythonTool()
        code = """
x = 1
y = 2
print(f"Sum: {x + y}")
"""
        result = tool.execute(code=code)

        assert result.success is True
        assert "Sum: 3" in result.output

    def test_run_python_timeout(self):
        """Test that long-running Python code times out."""
        tool = RunPythonTool(timeout=1)
        code = """
import time
time.sleep(5)
print("Should not reach here")
"""
        result = tool.execute(code=code)

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_run_python_with_special_characters(self):
        """Test running Python code with special characters."""
        tool = RunPythonTool()
        result = tool.execute(code="print('Hello \"World\"')")

        assert result.success is True
        assert "Hello" in result.output
