"""Tests for process management tools."""

import signal
from unittest.mock import MagicMock, patch

import pytest

from coding_agent.tools.process import (
    GetProcessInfoTool,
    ListProcessesTool,
    ProcessTools,
    StartProcessTool,
    StopProcessTool,
)
from coding_agent.tools.base import ToolResult


class TestProcessTools:
    """Tests for ProcessTools class."""

    def test_init_default_workspace(self):
        """Test initialization with default workspace."""
        tools = ProcessTools()
        assert tools.workspace_root is not None

    def test_init_custom_workspace(self):
        """Test initialization with custom workspace."""
        tools = ProcessTools(workspace_root="/tmp/test")
        assert str(tools.workspace_root).endswith("/tmp/test")


class TestStartProcessTool:
    """Tests for StartProcessTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = StartProcessTool()
        assert tool.name == "start_process"

    def test_description_property(self):
        """Test tool description."""
        tool = StartProcessTool()
        assert "background process" in tool.description.lower()
        assert "PID" in tool.description

    def test_schema_property(self):
        """Test tool schema."""
        tool = StartProcessTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "command" in schema["properties"]
        assert "command" in schema["required"]
        assert "name" in schema["properties"]

    def test_execute_missing_command(self):
        """Test execute with missing command parameter."""
        tool = StartProcessTool()
        result = tool.execute()
        
        assert result.success is False
        assert "Missing required parameter: command" in result.error

    @patch("coding_agent.tools.process.subprocess.Popen")
    def test_execute_success(self, mock_popen):
        """Test successful process start."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        tool = StartProcessTool()
        result = tool.execute(command="echo hello", name="test_process")
        
        assert result.success is True
        assert "12345" in result.output
        assert "test_process" in result.output
        mock_popen.assert_called_once()

    @patch("coding_agent.tools.process.subprocess.Popen")
    def test_execute_without_name(self, mock_popen):
        """Test starting process without a name."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        tool = StartProcessTool()
        result = tool.execute(command="echo hello")
        
        assert result.success is True
        assert "unnamed" in result.output

    @patch("coding_agent.tools.process.subprocess.Popen")
    def test_execute_raises_exception(self, mock_popen):
        """Test execute that raises an exception."""
        mock_popen.side_effect = Exception("Failed to start")
        
        tool = StartProcessTool()
        result = tool.execute(command="invalid_command")
        
        assert result.success is False
        assert "Failed to start" in result.error


class TestStopProcessTool:
    """Tests for StopProcessTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = StopProcessTool()
        assert tool.name == "stop_process"

    def test_description_property(self):
        """Test tool description."""
        tool = StopProcessTool()
        assert "SIGTERM" in tool.description
        assert "SIGKILL" in tool.description

    def test_schema_property(self):
        """Test tool schema."""
        tool = StopProcessTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "pid" in schema["properties"]
        assert "pid" in schema["required"]
        assert "force" in schema["properties"]

    def test_execute_missing_pid(self):
        """Test execute with missing PID parameter."""
        tool = StopProcessTool()
        result = tool.execute()
        
        assert result.success is False
        assert "Missing required parameter: pid" in result.error

    def test_execute_invalid_pid_format(self):
        """Test execute with invalid PID format."""
        tool = StopProcessTool()
        result = tool.execute(pid="not_a_number")
        
        assert result.success is False
        assert "Invalid PID" in result.error

    @patch("coding_agent.tools.process.os.kill")
    def test_execute_process_not_exists(self, mock_kill):
        """Test stopping a non-existent process."""
        mock_kill.side_effect = OSError("No such process")
        
        tool = StopProcessTool()
        result = tool.execute(pid=99999)
        
        assert result.success is False
        assert "does not exist" in result.error

    @patch("coding_agent.tools.process.os.kill")
    def test_execute_send_sigterm(self, mock_kill):
        """Test sending SIGTERM to process."""
        mock_kill.return_value = None  # No exception means success
        
        tool = StopProcessTool()
        result = tool.execute(pid=12345, force=False)
        
        assert result.success is True
        assert "SIGTERM" in result.output
        mock_kill.assert_called_with(12345, signal.SIGTERM)

    @patch("coding_agent.tools.process.os.kill")
    def test_execute_send_sigkill(self, mock_kill):
        """Test sending SIGKILL to process."""
        mock_kill.return_value = None
        
        tool = StopProcessTool()
        result = tool.execute(pid=12345, force=True)
        
        assert result.success is True
        assert "SIGKILL" in result.output
        mock_kill.assert_called_with(12345, signal.SIGKILL)

    @patch("coding_agent.tools.process.os.kill")
    def test_execute_permission_denied(self, mock_kill):
        """Test permission denied when stopping process."""
        # First call (os.kill(pid, 0)) succeeds - process exists
        # Second call (os.kill(pid, SIGTERM)) raises PermissionError
        mock_kill.side_effect = [None, PermissionError("Permission denied")]
        
        tool = StopProcessTool()
        result = tool.execute(pid=12345)
        
        assert result.success is False
        assert "Permission denied" in result.error


class TestListProcessesTool:
    """Tests for ListProcessesTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = ListProcessesTool()
        assert tool.name == "list_processes"

    def test_description_property(self):
        """Test tool description."""
        tool = ListProcessesTool()
        assert "List" in tool.description
        assert "process" in tool.description.lower()

    def test_schema_property(self):
        """Test tool schema."""
        tool = ListProcessesTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "pattern" in schema["properties"]
        assert "limit" in schema["properties"]

    @patch("coding_agent.tools.process.subprocess.run")
    def test_execute_success(self, mock_run):
        """Test listing processes successfully."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 169436 11772 ?        Ss   Jan01   0:02 /sbin/init
root       123  0.1  0.2 200000 20000 ?        S    Jan01   1:00 python app.py"""
        mock_run.return_value = mock_result
        
        tool = ListProcessesTool()
        result = tool.execute()
        
        assert result.success is True
        assert "process" in result.output.lower()

    @patch("coding_agent.tools.process.subprocess.run")
    def test_execute_with_pattern_filter(self, mock_run):
        """Test listing processes with pattern filter."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root       123  0.1  0.2 200000 20000 ?        S    Jan01   1:00 python app.py
root       456  0.2  0.3 300000 30000 ?        S    Jan01   2:00 node server.js"""
        mock_run.return_value = mock_result
        
        tool = ListProcessesTool()
        result = tool.execute(pattern="python")
        
        assert result.success is True
        # Should only contain python process
        assert "python" in result.output.lower()

    @patch("coding_agent.tools.process.subprocess.run")
    def test_execute_no_matching_processes(self, mock_run):
        """Test when no processes match the pattern."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 169436 11772 ?        Ss   Jan01   0:02 /sbin/init"""
        mock_run.return_value = mock_result
        
        tool = ListProcessesTool()
        result = tool.execute(pattern="nonexistent")
        
        assert result.success is True
        assert "No matching processes" in result.output

    @patch("coding_agent.tools.process.subprocess.run")
    def test_execute_ps_command_fails(self, mock_run):
        """Test when ps command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        tool = ListProcessesTool()
        result = tool.execute()
        
        assert result.success is False
        assert "Failed to retrieve" in result.error

    @patch("coding_agent.tools.process.subprocess.run")
    def test_execute_timeout(self, mock_run):
        """Test when ps command times out."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired(cmd="ps aux", timeout=10)
        
        tool = ListProcessesTool()
        result = tool.execute()
        
        assert result.success is False
        assert "Timed out" in result.error


class TestGetProcessInfoTool:
    """Tests for GetProcessInfoTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = GetProcessInfoTool()
        assert tool.name == "get_process_info"

    def test_description_property(self):
        """Test tool description."""
        tool = GetProcessInfoTool()
        assert "detailed information" in tool.description.lower()
        assert "PID" in tool.description

    def test_schema_property(self):
        """Test tool schema."""
        tool = GetProcessInfoTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "pid" in schema["properties"]
        assert "pid" in schema["required"]

    def test_execute_missing_pid(self):
        """Test execute with missing PID parameter."""
        tool = GetProcessInfoTool()
        result = tool.execute()
        
        assert result.success is False
        assert "Missing required parameter: pid" in result.error

    def test_execute_invalid_pid_format(self):
        """Test execute with invalid PID format."""
        tool = GetProcessInfoTool()
        result = tool.execute(pid="not_a_number")
        
        assert result.success is False
        assert "Invalid PID" in result.error

    @patch("coding_agent.tools.process.os.kill")
    @patch("coding_agent.tools.process.subprocess.run")
    def test_execute_success(self, mock_run, mock_kill):
        """Test getting process info successfully."""
        mock_kill.return_value = None  # Process exists
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """  PID  PPID USER     STAT STARTED ELAPSED CMD
  1234     1 root     S    09:00:00 01:00:00 python app.py"""
        mock_run.return_value = mock_result
        
        tool = GetProcessInfoTool()
        result = tool.execute(pid=1234)
        
        assert result.success is True
        assert "1234" in result.output
        assert "Process Information" in result.output

    @patch("coding_agent.tools.process.os.kill")
    def test_execute_process_not_exists(self, mock_kill):
        """Test getting info for non-existent process."""
        mock_kill.side_effect = OSError("No such process")
        
        tool = GetProcessInfoTool()
        result = tool.execute(pid=99999)
        
        assert result.success is False
        assert "does not exist" in result.error

    @patch("coding_agent.tools.process.os.kill")
    @patch("coding_agent.tools.process.subprocess.run")
    def test_execute_ps_command_fails(self, mock_run, mock_kill):
        """Test when ps command fails."""
        mock_kill.return_value = None
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        tool = GetProcessInfoTool()
        result = tool.execute(pid=1234)
        
        assert result.success is False
        assert "Failed to get info" in result.error

    @patch("coding_agent.tools.process.os.kill")
    @patch("coding_agent.tools.process.subprocess.run")
    def test_execute_timeout(self, mock_run, mock_kill):
        """Test when ps command times out."""
        from subprocess import TimeoutExpired
        mock_kill.return_value = None
        mock_run.side_effect = TimeoutExpired(cmd="ps", timeout=10)
        
        tool = GetProcessInfoTool()
        result = tool.execute(pid=1234)
        
        assert result.success is False
        assert "Timed out" in result.error
