"""Tests for the filesystem tools."""

import os
import tempfile
from pathlib import Path

import pytest

from coding_agent.tools.filesystem import (
    FileSystemTools,
    ListDirTool,
    ReadFileTool,
    SearchFilesTool,
    WriteFileTool,
)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestFileSystemTools:
    """Tests for the FileSystemTools helper class."""

    def test_safe_path_within_workspace(self, temp_workspace):
        """Test that safe_path returns correct path for valid input."""
        fs_tools = FileSystemTools(workspace_root=temp_workspace)
        result = fs_tools._safe_path("subdir/file.txt")
        assert str(result).startswith(temp_workspace)
        assert result.name == "file.txt"

    def test_safe_path_raises_error_for_escape(self, temp_workspace):
        """Test that safe_path raises ValueError for path traversal attempts."""
        fs_tools = FileSystemTools(workspace_root=temp_workspace)
        with pytest.raises(ValueError, match="outside workspace"):
            fs_tools._safe_path("../etc/passwd")


class TestReadFileTool:
    """Tests for the ReadFileTool class."""

    def test_read_existing_file(self, temp_workspace):
        """Test reading an existing file."""
        # Create a test file
        test_file = Path(temp_workspace) / "test.txt"
        test_file.write_text("Hello, World!")

        tool = ReadFileTool(workspace_root=temp_workspace)
        result = tool.execute(path="test.txt")

        assert result.success is True
        assert result.output == "Hello, World!"

    def test_read_nonexistent_file(self, temp_workspace):
        """Test reading a file that doesn't exist."""
        tool = ReadFileTool(workspace_root=temp_workspace)
        result = tool.execute(path="nonexistent.txt")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_read_directory_fails(self, temp_workspace):
        """Test that reading a directory fails."""
        dir_path = Path(temp_workspace) / "testdir"
        dir_path.mkdir()

        tool = ReadFileTool(workspace_root=temp_workspace)
        result = tool.execute(path="testdir")

        assert result.success is False
        assert "not a file" in result.error.lower()

    def test_read_missing_path_parameter(self, temp_workspace):
        """Test that missing path parameter returns error."""
        tool = ReadFileTool(workspace_root=temp_workspace)
        result = tool.execute()

        assert result.success is False
        assert "path" in result.error.lower()


class TestWriteFileTool:
    """Tests for the WriteFileTool class."""

    def test_write_new_file(self, temp_workspace):
        """Test writing to a new file."""
        tool = WriteFileTool(workspace_root=temp_workspace)
        result = tool.execute(path="output.txt", content="Test content")

        assert result.success is True
        written_file = Path(temp_workspace) / "output.txt"
        assert written_file.exists()
        assert written_file.read_text() == "Test content"

    def test_write_overwrites_existing_file(self, temp_workspace):
        """Test that writing overwrites existing file content."""
        # Create initial file
        test_file = Path(temp_workspace) / "overwrite.txt"
        test_file.write_text("Original content")

        tool = WriteFileTool(workspace_root=temp_workspace)
        result = tool.execute(path="overwrite.txt", content="New content")

        assert result.success is True
        assert test_file.read_text() == "New content"

    def test_write_creates_parent_directories(self, temp_workspace):
        """Test that write_file creates parent directories if needed."""
        tool = WriteFileTool(workspace_root=temp_workspace)
        result = tool.execute(path="nested/dir/file.txt", content="Nested content")

        assert result.success is True
        written_file = Path(temp_workspace) / "nested" / "dir" / "file.txt"
        assert written_file.exists()
        assert written_file.read_text() == "Nested content"

    def test_write_missing_path_parameter(self, temp_workspace):
        """Test that missing path parameter returns error."""
        tool = WriteFileTool(workspace_root=temp_workspace)
        result = tool.execute(content="Some content")

        assert result.success is False
        assert "path" in result.error.lower()

    def test_write_missing_content_parameter(self, temp_workspace):
        """Test that missing content parameter returns error."""
        tool = WriteFileTool(workspace_root=temp_workspace)
        result = tool.execute(path="file.txt")

        assert result.success is False
        assert "content" in result.error.lower()


class TestListDirTool:
    """Tests for the ListDirTool class."""

    def test_list_empty_directory(self, temp_workspace):
        """Test listing an empty directory."""
        dir_path = Path(temp_workspace) / "empty_dir"
        dir_path.mkdir()

        tool = ListDirTool(workspace_root=temp_workspace)
        result = tool.execute(path="empty_dir")

        assert result.success is True
        assert "empty" in result.output.lower()

    def test_list_directory_with_files(self, temp_workspace):
        """Test listing a directory containing files."""
        dir_path = Path(temp_workspace) / "files_dir"
        dir_path.mkdir()
        (dir_path / "file1.txt").write_text("content1")
        (dir_path / "file2.txt").write_text("content2")

        tool = ListDirTool(workspace_root=temp_workspace)
        result = tool.execute(path="files_dir")

        assert result.success is True
        assert "file1.txt" in result.output
        assert "file2.txt" in result.output

    def test_list_directory_with_subdirectories(self, temp_workspace):
        """Test listing a directory containing subdirectories."""
        dir_path = Path(temp_workspace) / "mixed_dir"
        dir_path.mkdir()
        (dir_path / "subdir").mkdir()
        (dir_path / "file.txt").write_text("content")

        tool = ListDirTool(workspace_root=temp_workspace)
        result = tool.execute(path="mixed_dir")

        assert result.success is True
        assert "[DIR] subdir" in result.output
        assert "file.txt" in result.output

    def test_list_nonexistent_directory(self, temp_workspace):
        """Test listing a directory that doesn't exist."""
        tool = ListDirTool(workspace_root=temp_workspace)
        result = tool.execute(path="nonexistent_dir")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_list_file_instead_of_directory(self, temp_workspace):
        """Test that listing a file fails."""
        file_path = Path(temp_workspace) / "afile.txt"
        file_path.write_text("content")

        tool = ListDirTool(workspace_root=temp_workspace)
        result = tool.execute(path="afile.txt")

        assert result.success is False
        assert "not a directory" in result.error.lower()

    def test_list_missing_path_parameter(self, temp_workspace):
        """Test that missing path parameter returns error."""
        tool = ListDirTool(workspace_root=temp_workspace)
        result = tool.execute()

        assert result.success is False
        assert "path" in result.error.lower()


class TestSearchFilesTool:
    """Tests for the SearchFilesTool class."""

    def test_search_files_by_extension(self, temp_workspace):
        """Test searching for files by extension."""
        # Create test files
        (Path(temp_workspace) / "file1.py").write_text("# Python")
        (Path(temp_workspace) / "file2.py").write_text("# Python")
        (Path(temp_workspace) / "file.txt").write_text("Text")

        tool = SearchFilesTool(workspace_root=temp_workspace)
        result = tool.execute(pattern="*.py")

        assert result.success is True
        assert "file1.py" in result.output
        assert "file2.py" in result.output
        assert "file.txt" not in result.output

    def test_search_no_matches(self, temp_workspace):
        """Test searching with no matches."""
        tool = SearchFilesTool(workspace_root=temp_workspace)
        result = tool.execute(pattern="*.nonexistent")

        assert result.success is True
        assert "no matches" in result.output.lower()

    def test_search_recursive_pattern(self, temp_workspace):
        """Test recursive glob pattern search."""
        # Create nested structure
        nested = Path(temp_workspace) / "level1" / "level2"
        nested.mkdir(parents=True)
        (nested / "deep.py").write_text("# Deep file")

        tool = SearchFilesTool(workspace_root=temp_workspace)
        result = tool.execute(pattern="**/*.py")

        assert result.success is True
        assert "deep.py" in result.output

    def test_search_missing_pattern_parameter(self, temp_workspace):
        """Test that missing pattern parameter returns error."""
        tool = SearchFilesTool(workspace_root=temp_workspace)
        result = tool.execute()

        assert result.success is False
        assert "pattern" in result.error.lower()
