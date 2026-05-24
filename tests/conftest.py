"""Shared pytest fixtures and configuration for coding_agent tests."""

import sys
from pathlib import Path

import pytest

# Add the workspace root to the Python path
workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))


@pytest.fixture(scope="session")
def test_workspace():
    """Provide a test workspace directory."""
    return str(workspace_root)
