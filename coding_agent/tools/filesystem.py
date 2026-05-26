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


class GetTreeTool(Tool):
    """Tool for getting a tree view of files and directories."""

    def __init__(self, workspace_root: str = ".", max_depth: int = 3) -> None:
        """Initialize the get tree tool.

        Args:
            workspace_root: Root directory for file operations.
            max_depth: Maximum depth to traverse (default: 3).
        """
        self._fs_tools = FileSystemTools(workspace_root)
        self._max_depth = max_depth

    @property
    def name(self) -> str:
        """Return tool name."""
        return "get_tree"

    @property
    def description(self) -> str:
        """Return tool description."""
        return "Get a tree view of files and directories from the current directory. Shows the hierarchical structure with optional depth control."

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the directory from workspace root (default: current directory)",
                },
                "max_depth": {
                    "type": "integer",
                    "description": f"Maximum depth to traverse (default: {self._max_depth})",
                },
            },
            "required": [],
        }

    def _build_tree(self, dir_path: Path, prefix: str = "", depth: int = 0, max_depth: int = 3) -> list[str]:
        """Build tree representation recursively.

        Args:
            dir_path: Directory path to traverse.
            prefix: Current prefix string for indentation.
            depth: Current depth level.
            max_depth: Maximum depth to traverse.

        Returns:
            List of strings representing the tree.
        """
        result = []
        
        if depth > max_depth:
            return result
        
        try:
            items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return [f"{prefix}[Permission Denied]"]
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            
            if item.is_dir():
                result.append(f"{prefix}{connector}[DIR] {item.name}")
                extension = "    " if is_last else "│   "
                result.extend(self._build_tree(item, prefix + extension, depth + 1, max_depth))
            else:
                result.append(f"{prefix}{connector}{item.name}")
        
        return result

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the get tree operation.

        Args:
            **kwargs: Optional 'path' and 'max_depth' keys.

        Returns:
            ToolResult with tree output or error.
        """
        try:
            path = kwargs.get("path", ".")
            max_depth = kwargs.get("max_depth", self._max_depth)

            dir_path = self._fs_tools._safe_path(path)

            if not dir_path.exists():
                return ToolResult(success=False, error=f"Directory not found: {path}")

            if not dir_path.is_dir():
                return ToolResult(success=False, error=f"Not a directory: {path}")

            # Add root directory name
            root_name = dir_path.name if dir_path.name else str(dir_path)
            tree_lines = [f"[DIR] {root_name}"]
            
            # Build tree structure
            tree_lines.extend(self._build_tree(dir_path, "", 0, max_depth))
            
            output = "\n".join(tree_lines)
            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(success=False, error=str(e))
