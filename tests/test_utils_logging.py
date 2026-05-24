"""Tests for the logging configuration."""

import logging
import tempfile
from pathlib import Path

import pytest

from coding_agent.utils.logging_config import setup_logging


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_default_level(self):
        """Test setting up logging with default level."""
        setup_logging(level="INFO")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_logging_debug_level(self):
        """Test setting up logging with DEBUG level."""
        setup_logging(level="DEBUG")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_error_level(self):
        """Test setting up logging with ERROR level."""
        setup_logging(level="ERROR")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.ERROR

    def test_setup_logging_with_file(self):
        """Test setting up logging with a file handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logging(level="INFO", log_file=str(log_file))

            # Log something
            logging.info("Test log message")

            # Flush handlers
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                handler.flush()

            assert log_file.exists()
            content = log_file.read_text()
            assert "Test log message" in content

    def test_setup_logging_custom_format(self):
        """Test setting up logging with custom format."""
        custom_format = "[CUSTOM] %(levelname)s - %(message)s"
        setup_logging(level="INFO", format_string=custom_format)

        root_logger = logging.getLogger()
        # Check that at least one handler has the custom format
        found_custom = False
        for handler in root_logger.handlers:
            if hasattr(handler, "formatter"):
                fmt = handler.formatter._fmt
                if "[CUSTOM]" in str(fmt):
                    found_custom = True
                    break
        assert found_custom

    def test_setup_logging_clears_existing_handlers(self):
        """Test that setup_logging clears existing handlers."""
        # Add a dummy handler first
        root_logger = logging.getLogger()
        initial_handler_count = len(root_logger.handlers)
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)

        # Setup logging should clear handlers
        setup_logging(level="INFO")

        # The count should be reset (typically 1 console handler, or 2 if file specified)
        assert len(root_logger.handlers) <= 2

        # Dummy handler should be removed
        assert dummy_handler not in root_logger.handlers

    def test_setup_logging_httpx_warning(self):
        """Test that httpx logger is set to WARNING."""
        setup_logging(level="INFO")

        httpx_logger = logging.getLogger("httpx")
        assert httpx_logger.level == logging.WARNING

    def test_setup_logging_httpcore_warning(self):
        """Test that httpcore logger is set to WARNING."""
        setup_logging(level="INFO")

        httpcore_logger = logging.getLogger("httpcore")
        assert httpcore_logger.level == logging.WARNING

    def test_setup_logging_case_insensitive_level(self):
        """Test that log level is case-insensitive."""
        setup_logging(level="debug")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

        setup_logging(level="Warning")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_setup_logging_multiple_handlers_with_file(self):
        """Test that both console and file handlers are added when file specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logging(level="INFO", log_file=str(log_file))

            root_logger = logging.getLogger()
            # Should have at least 2 handlers: console + file
            assert len(root_logger.handlers) >= 2
