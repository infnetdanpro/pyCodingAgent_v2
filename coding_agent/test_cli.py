#!/usr/bin/env python3
"""Tests for the coding agent CLI module."""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from coding_agent.cli import cmd_chat, cmd_init, cmd_run, create_agent, main


class TestCreateAgent:
    """Tests for the create_agent function."""

    def test_create_agent_returns_coding_agent(self):
        """Test that create_agent returns a CodingAgent instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from coding_agent.config import ModelConfig
            model_config = ModelConfig(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model_name="qwen2.5-coder:7b",
            )
            agent = create_agent(tmpdir, model_config)
            
            # Check that agent has expected attributes/methods
            assert hasattr(agent, 'register_tool')
            assert hasattr(agent, 'tool_registry')

    def test_create_agent_registers_tools(self):
        """Test that create_agent registers all default tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from coding_agent.config import ModelConfig
            model_config = ModelConfig(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model_name="qwen2.5-coder:7b",
            )
            agent = create_agent(tmpdir, model_config)
            
            # Check that tools are registered
            registered_tools = agent.tool_registry.list_tools()
            expected_tools = [
                'read_file',
                'write_file',
                'list_dir',
                'search_files',
                'run_command',
                'run_python',
            ]
            for tool in expected_tools:
                assert tool in registered_tools


class TestCmdInit:
    """Tests for the cmd_init function."""

    def test_cmd_init_creates_directory(self):
        """Test that cmd_init creates a new directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new_project"
            args = argparse.Namespace(directory=str(new_dir))
            
            result = cmd_init(args)
            
            assert result == 0
            assert new_dir.exists()

    def test_cmd_init_creates_config_file(self):
        """Test that cmd_init creates .agent_config.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "test_project"
            args = argparse.Namespace(directory=str(target_dir))
            
            cmd_init(args)
            
            config_file = target_dir / ".agent_config.json"
            assert config_file.exists()
            
            with open(config_file) as f:
                config = json.load(f)
            
            assert "workspace_dir" in config
            assert "model" in config
            assert config["model"]["base_url"] == "http://localhost:11434/v1"
            assert config["model"]["api_key"] == "ollama"
            assert config["model"]["model_name"] == "qwen2.5-coder:7b"

    def test_cmd_init_creates_gitignore(self):
        """Test that cmd_init creates .gitignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "test_project"
            args = argparse.Namespace(directory=str(target_dir))
            
            cmd_init(args)
            
            gitignore_file = target_dir / ".gitignore"
            assert gitignore_file.exists()
            
            with open(gitignore_file) as f:
                content = f.read()
            
            assert ".agent_history/" in content
            assert "__pycache__/" in content
            assert "*.pyc" in content

    def test_cmd_init_existing_directory(self):
        """Test cmd_init with an existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            args = argparse.Namespace(directory=str(target_dir))
            
            result = cmd_init(args)
            
            assert result == 0

    def test_cmd_init_config_already_exists(self):
        """Test that cmd_init doesn't overwrite existing config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            config_file = target_dir / ".agent_config.json"
            
            # Create existing config with custom content
            custom_config = {"custom": "value"}
            with open(config_file, 'w') as f:
                json.dump(custom_config, f)
            
            args = argparse.Namespace(directory=str(target_dir))
            cmd_init(args)
            
            # Verify original content is preserved
            with open(config_file) as f:
                config = json.load(f)
            
            assert config == custom_config

    def test_cmd_init_default_directory(self):
        """Test cmd_init with default current directory argument."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                args = argparse.Namespace(directory=".")
                
                result = cmd_init(args)
                
                assert result == 0
                assert (Path(tmpdir) / ".agent_config.json").exists()
            finally:
                os.chdir(original_cwd)


class TestCmdChat:
    """Tests for the cmd_chat function."""

    def test_cmd_chat_nonexistent_workspace(self):
        """Test cmd_chat with non-existent workspace."""
        args = argparse.Namespace(
            workspace="/nonexistent/path",
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model="qwen2.5-coder:7b",
            log_level="INFO",
        )
        
        result = cmd_chat(args)
        
        assert result == 1

    @patch('coding_agent.cli.create_agent')
    @patch('builtins.input', side_effect=['/quit'])
    def test_cmd_chat_quit_command(self, mock_input, mock_create_agent):
        """Test cmd_chat with quit command."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            assert result == 0

    @patch('coding_agent.cli.create_agent')
    @patch('builtins.input', side_effect=['/help', '/quit'])
    def test_cmd_chat_help_command(self, mock_input, mock_create_agent):
        """Test cmd_chat with help command."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            assert result == 0

    @patch('coding_agent.cli.create_agent')
    @patch('builtins.input', side_effect=['/tools', '/quit'])
    def test_cmd_chat_tools_command(self, mock_input, mock_create_agent):
        """Test cmd_chat with tools command."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_agent.tool_registry.list_tools.return_value = ['ReadFileTool', 'WriteFileTool']
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            assert result == 0

    @patch('coding_agent.cli.create_agent')
    @patch('builtins.input', side_effect=['/clear', '/quit'])
    def test_cmd_chat_clear_command(self, mock_input, mock_create_agent):
        """Test cmd_chat with clear command."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            mock_agent.clear_context.assert_called_once()
            assert result == 0

    @patch('coding_agent.cli.create_agent')
    @patch('builtins.input', side_effect=['/unknown', '/quit'])
    def test_cmd_chat_unknown_command(self, mock_input, mock_create_agent):
        """Test cmd_chat with unknown command."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            assert result == 0

    @patch('coding_agent.cli.create_agent')
    @patch('builtins.input', side_effect=['Test message', '/quit'])
    def test_cmd_chat_normal_message(self, mock_input, mock_create_agent):
        """Test cmd_chat with normal message."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_agent.run.return_value = "Response from agent"
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            mock_agent.run.assert_called_once_with('Test message')
            assert result == 0

    @patch('coding_agent.cli.create_agent')
    @patch('builtins.input', side_effect=['Test message', '/quit'])
    def test_cmd_chat_agent_error(self, mock_input, mock_create_agent):
        """Test cmd_chat when agent.run raises an exception."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_agent.run.side_effect = Exception("Agent error")
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            assert result == 0  # Should continue running despite error

    @patch('coding_agent.cli.create_agent')
    @patch('builtins.input', side_effect=EOFError())
    def test_cmd_chat_eof_error(self, mock_input, mock_create_agent):
        """Test cmd_chat handles EOFError."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            assert result == 0

    @patch('coding_agent.cli.create_agent')
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_cmd_chat_keyboard_interrupt(self, mock_input, mock_create_agent):
        """Test cmd_chat handles KeyboardInterrupt."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            assert result == 0

    @patch('coding_agent.cli.create_agent')
    def test_cmd_chat_initialization_error(self, mock_create_agent):
        """Test cmd_chat when agent initialization fails."""
        mock_create_agent.side_effect = Exception("Initialization failed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_chat(args)
            
            assert result == 1

    def test_cmd_chat_various_quit_commands(self):
        """Test various quit command variations."""
        quit_commands = ['/quit', '/exit', 'quit', 'exit', 'q']
        
        for quit_cmd in quit_commands:
            with patch('coding_agent.cli.create_agent') as mock_create_agent:
                with patch('builtins.input', side_effect=[quit_cmd]):
                    mock_agent = MagicMock()
                    mock_agent.__enter__ = MagicMock(return_value=mock_agent)
                    mock_agent.__exit__ = MagicMock(return_value=False)
                    mock_create_agent.return_value = mock_agent
                    
                    with tempfile.TemporaryDirectory() as tmpdir:
                        args = argparse.Namespace(
                            workspace=tmpdir,
                            base_url="http://localhost:11434/v1",
                            api_key="ollama",
                            model="qwen2.5-coder:7b",
                            log_level="INFO",
                        )
                        
                        result = cmd_chat(args)
                        assert result == 0


class TestCmdRun:
    """Tests for the cmd_run function."""

    def test_cmd_run_nonexistent_workspace(self):
        """Test cmd_run with non-existent workspace."""
        args = argparse.Namespace(
            command="test command",
            workspace="/nonexistent/path",
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model="qwen2.5-coder:7b",
            log_level="INFO",
        )
        
        result = cmd_run(args)
        
        assert result == 1

    @patch('coding_agent.cli.create_agent')
    def test_cmd_run_success(self, mock_create_agent):
        """Test cmd_run successful execution."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_agent.run.return_value = "Command output"
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                command="test command",
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_run(args)
            
            mock_agent.run.assert_called_once_with("test command")
            assert result == 0

    @patch('coding_agent.cli.create_agent')
    def test_cmd_run_agent_error(self, mock_create_agent):
        """Test cmd_run when agent raises an exception."""
        mock_agent = MagicMock()
        mock_agent.__enter__ = MagicMock(return_value=mock_agent)
        mock_agent.__exit__ = MagicMock(return_value=False)
        mock_agent.run.side_effect = Exception("Agent error")
        mock_create_agent.return_value = mock_agent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                command="test command",
                workspace=tmpdir,
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="qwen2.5-coder:7b",
                log_level="INFO",
            )
            
            result = cmd_run(args)
            
            assert result == 1


class TestMain:
    """Tests for the main function."""

    def test_main_no_command_shows_help(self, capsys):
        """Test that main shows help when no command is provided."""
        with patch('sys.argv', ['agent']):
            result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out or "help" in captured.out.lower()

    def test_main_init_command(self, capsys):
        """Test main with init command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('sys.argv', ['agent', 'init', tmpdir]):
                result = main()
            
            assert result == 0
            assert (Path(tmpdir) / ".agent_config.json").exists()

    def test_main_chat_command(self, capsys):
        """Test main with chat command."""
        # Use --help which exits cleanly with code 0
        with patch('sys.argv', ['agent', 'chat', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_run_command(self, capsys):
        """Test main with run command."""
        # Use --help which exits cleanly with code 0
        with patch('sys.argv', ['agent', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_help_flag(self, capsys):
        """Test main with --help flag."""
        with patch('sys.argv', ['agent', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "help" in captured.out.lower()

    def test_main_init_with_custom_directory(self, capsys):
        """Test main with init command and custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "custom_dir"
            with patch('sys.argv', ['agent', 'init', str(new_dir)]):
                result = main()
            
            assert result == 0
            assert new_dir.exists()

    def test_main_chat_with_options(self, capsys):
        """Test main with chat command and options."""
        # Use --help to avoid actually starting the chat session
        with patch('sys.argv', [
            'agent', 'chat',
            '--workspace', '.',
            '--base-url', 'http://test:11434/v1',
            '--api-key', 'test-key',
            '--model', 'test-model',
            '--log-level', 'DEBUG',
            '--help'
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_run_with_options(self, capsys):
        """Test main with run command and options."""
        # Use --help to avoid actually running a command
        with patch('sys.argv', [
            'agent', 'run',
            'test command',
            '--workspace', '.',
            '--base-url', 'http://test:11434/v1',
            '--api-key', 'test-key',
            '--model', 'test-model',
            '--log-level', 'DEBUG',
            '--help'
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestArgumentParsing:
    """Tests for argument parsing."""

    def test_init_parser_defaults(self):
        """Test init parser default values."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        init_parser = subparsers.add_parser("init")
        init_parser.add_argument("directory", nargs="?", default=".")
        init_parser.set_defaults(func=lambda x: 0)
        
        args = parser.parse_args(['init'])
        assert args.directory == "."
        
        args = parser.parse_args(['init', '/custom/path'])
        assert args.directory == "/custom/path"

    def test_chat_parser_defaults(self):
        """Test chat parser default values."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        chat_parser = subparsers.add_parser("chat")
        chat_parser.add_argument("-w", "--workspace", default=".")
        chat_parser.add_argument("--base-url", default="http://localhost:11434/v1")
        chat_parser.add_argument("--api-key", default="ollama")
        chat_parser.add_argument("--model", default="qwen2.5-coder:7b")
        chat_parser.add_argument("--log-level", default="INFO")
        chat_parser.set_defaults(func=lambda x: 0)
        
        args = parser.parse_args(['chat'])
        assert args.workspace == "."
        assert args.base_url == "http://localhost:11434/v1"
        assert args.api_key == "ollama"
        assert args.model == "qwen2.5-coder:7b"
        assert args.log_level == "INFO"

    def test_run_parser_defaults(self):
        """Test run parser default values."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        run_parser = subparsers.add_parser("run")
        run_parser.add_argument("command")
        run_parser.add_argument("-w", "--workspace", default=".")
        run_parser.add_argument("--base-url", default="http://localhost:11434/v1")
        run_parser.add_argument("--api-key", default="ollama")
        run_parser.add_argument("--model", default="qwen2.5-coder:7b")
        run_parser.add_argument("--log-level", default="INFO")
        run_parser.set_defaults(func=lambda x: 0)
        
        args = parser.parse_args(['run', 'test'])
        assert args.command == "test"
        assert args.workspace == "."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
