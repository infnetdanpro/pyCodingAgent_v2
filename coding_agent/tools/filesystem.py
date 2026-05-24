"""File system tools for the coding agent."""

import os
from pathlib import Path
from typing import Any

from .base import Tool, ToolResult


class FileSystemTools:
    """Collection of file system operation tools.

    Provides safe file operations with workspace isolation.
    """

    def __init__(self, workspace_root: str = ".") -> None:
        """Initialize file system tools.

        Args:
            workspace_root: Root directory for file operations.
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _safe_path(self, path: str) -> Path:
        """Ensure path is within workspace root.

        Args:
            path: User-provided path.

        Returns:
            Resolved Path within workspace.

        Raises:
            ValueError: If path is outside workspace.
        """
        resolved = (self.workspace_root / path).resolve()
        if not str(resolved).startswith(str(self.workspace_root)):
            raise ValueError(f"Path '{path}' is outside workspace")
        return resolved


class ReadFileTool(Tool):
    """Tool for reading file contents."""

    def __init__(self, workspace_root: str = ".") -> None:
        """Initialize the read file tool.

        Args:
            workspace_root: Root directory for file operations.
        """
        self._fs_tools = FileSystemTools(workspace_root)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "read_file"

    @property
    def description(self) -> str:
        """Return tool description."""
        return "Read contents of a file. Use this to examine existing code or configuration files."

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the file from workspace root",
                },
            },
            "required": ["path"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the read file operation.

        Args:
            **kwargs: Must contain 'path' key.

        Returns:
            ToolResult with file contents or error.
        """
        try:
            path = kwargs.get("path")
            if not path:
                return ToolResult(success=False, error="Missing required parameter: path")

            file_path = self._fs_tools._safe_path(path)

            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")

            if not file_path.is_file():
                return ToolResult(success=False, error=f"Not a file: {path}")

            content = file_path.read_text(encoding="utf-8")
            return ToolResult(success=True, output=content)

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteFileTool(Tool):
    """Tool for writing files."""

    def __init__(self, workspace_root: str = ".") -> None:
        """Initialize the write file tool.

        Args:
            workspace_root: Root directory for file operations.
        """
        self._fs_tools = FileSystemTools(workspace_root)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "write_file"

    @property
    def description(self) -> str:
        """Return tool description."""
        return "Write content to a file. Creates parent directories if needed. Overwrites existing files."

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the file from workspace root",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the write file operation.

        Args:
            **kwargs: Must contain 'path' and 'content' keys.

        Returns:
            ToolResult with success status or error.
        """
        try:
            path = kwargs.get("path")
            content = kwargs.get("content")

            if not path:
                return ToolResult(success=False, error="Missing required parameter: path")
            if content is None:
                return ToolResult(success=False, error="Missing required parameter: content")

            file_path = self._fs_tools._safe_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

            return ToolResult(success=True, output=f"Successfully wrote to {path}")

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListDirTool(Tool):
    """Tool for listing directory contents."""

    def __init__(self, workspace_root: str = ".") -> None:
        """Initialize the list directory tool.

        Args:
            workspace_root: Root directory for file operations.
        """
        self._fs_tools = FileSystemTools(workspace_root)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "list_dir"

    @property
    def description(self) -> str:
        """Return tool description."""
        return "List contents of a directory. Shows files and subdirectories."

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the directory from workspace root",
                },
            },
            "required": ["path"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the list directory operation.

        Args:
            **kwargs: Must contain 'path' key.

        Returns:
            ToolResult with directory listing or error.
        """
        try:
            path = kwargs.get("path")
            if not path:
                return ToolResult(success=False, error="Missing required parameter: path")

            dir_path = self._fs_tools._safe_path(path)

            if not dir_path.exists():
                return ToolResult(success=False, error=f"Directory not found: {path}")

            if not dir_path.is_dir():
                return ToolResult(success=False, error=f"Not a directory: {path}")

            items = []
            for item in sorted(dir_path.iterdir()):
                prefix = "[DIR] " if item.is_dir() else ""
                items.append(f"{prefix}{item.name}")

            output = "\n".join(items) if items else "(empty directory)"
            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SearchFilesTool(Tool):
    """Tool for searching files by pattern."""

    def __init__(self, workspace_root: str = ".") -> None:
        """Initialize the search files tool.

        Args:
            workspace_root: Root directory for file operations.
        """
        self._fs_tools = FileSystemTools(workspace_root)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "search_files"

    @property
    def description(self) -> str:
        """Return tool description."""
        return "Search for files matching a glob pattern. Useful for finding specific files."

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '*.py', '**/*.txt')",
                },
            },
            "required": ["pattern"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the search files operation.

        Args:
            **kwargs: Must contain 'pattern' key.

        Returns:
            ToolResult with matching files or error.
        """
        try:
            pattern = kwargs.get("pattern")
            if not pattern:
                return ToolResult(success=False, error="Missing required parameter: pattern")

            matches = list(self._fs_tools.workspace_root.glob(pattern))
            relative_paths = [str(m.relative_to(self._fs_tools.workspace_root)) for m in matches]

            output = "\n".join(relative_paths) if relative_paths else "(no matches found)"
            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(success=False, error=str(e))
