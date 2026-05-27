"""Git operations tools for the coding agent."""

import subprocess
from typing import Any, Optional

from .base import Tool, ToolResult


class GitTools:
    """Collection of Git operation tools.

    Provides safe Git operations with proper error handling and output capture.
    """

    def __init__(self, workspace_root: str = ".", timeout: int = 300) -> None:
        """Initialize git tools.

        Args:
            workspace_root: Working directory for Git operations.
            timeout: Default timeout for Git operations in seconds.
        """
        self.workspace_root = workspace_root
        self.timeout = timeout

    def _run_git(self, args: list[str], timeout: Optional[int] = None) -> ToolResult:
        """Run a Git command with the given arguments.

        Args:
            args: List of Git command arguments (without 'git').
            timeout: Optional timeout override.

        Returns:
            ToolResult with command output or error.
        """
        try:
            timeout = timeout if timeout is not None else self.timeout
            
            result = subprocess.run(
                ["git"] + args,
                shell=False,
                cwd=self.workspace_root,
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
                error=None if success else f"Git command failed with code {result.returncode}",
            )

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error=f"Git command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitDiffTool(Tool):
    """Tool for checking git diff against main/master branch."""

    def __init__(self, workspace_root: str = ".", timeout: int = 300) -> None:
        """Initialize the git diff tool.

        Args:
            workspace_root: Working directory for Git operations.
            timeout: Timeout for Git operation in seconds.
        """
        self._git_tools = GitTools(workspace_root, timeout)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "git_diff"

    @property
    def description(self) -> str:
        """Return tool description."""
        return (
            "Check git diff between current branch and main/master branch. "
            "Shows all changes made in the current branch compared to the base branch. "
            "Automatically detects whether to use 'main' or 'master' as the base branch."
        )

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "base_branch": {
                    "type": "string",
                    "description": "Base branch to compare against (optional, auto-detects main/master if not specified)",
                },
                "cached": {
                    "type": "boolean",
                    "description": "Whether to show staged changes only (default: false)",
                },
            },
            "required": [],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the git diff command.

        Args:
            **kwargs: Optional 'base_branch' and 'cached' parameters.

        Returns:
            ToolResult with diff output or error.
        """
        try:
            base_branch = kwargs.get("base_branch")
            cached = kwargs.get("cached", False)

            # Auto-detect base branch if not specified
            if not base_branch:
                detect_result = self._git_tools._run_git(["branch", "--list", "main"])
                if detect_result.success and detect_result.output.strip():
                    base_branch = "main"
                else:
                    base_branch = "master"

            # Build git diff command
            args = ["diff"]
            if cached:
                args.append("--cached")
            args.append(base_branch)

            return self._git_tools._run_git(args)

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitCommitTool(Tool):
    """Tool for creating git commits."""

    def __init__(self, workspace_root: str = ".", timeout: int = 300) -> None:
        """Initialize the git commit tool.

        Args:
            workspace_root: Working directory for Git operations.
            timeout: Timeout for Git operation in seconds.
        """
        self._git_tools = GitTools(workspace_root, timeout)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "git_commit"

    @property
    def description(self) -> str:
        """Return tool description."""
        return (
            "Create a git commit with the specified message. "
            "Optionally stage all changes before committing. "
            "Supports conventional commit format."
        )

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Commit message",
                },
                "all_files": {
                    "type": "boolean",
                    "description": "Whether to stage all changed files before committing (default: false)",
                },
            },
            "required": ["message"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the git commit command.

        Args:
            **kwargs: Must contain 'message', optionally 'all_files'.

        Returns:
            ToolResult with commit output or error.
        """
        try:
            message = kwargs.get("message")
            all_files = kwargs.get("all_files", False)

            if not message:
                return ToolResult(success=False, error="Missing required parameter: message")

            # Stage all files if requested
            if all_files:
                stage_result = self._git_tools._run_git(["add", "-A"])
                if not stage_result.success:
                    return stage_result

            # Create commit
            return self._git_tools._run_git(["commit", "-m", message])

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitPushTool(Tool):
    """Tool for pushing git commits to remote."""

    def __init__(self, workspace_root: str = ".", timeout: int = 300) -> None:
        """Initialize the git push tool.

        Args:
            workspace_root: Working directory for Git operations.
            timeout: Timeout for Git operation in seconds.
        """
        self._git_tools = GitTools(workspace_root, timeout)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "git_push"

    @property
    def description(self) -> str:
        """Return tool description."""
        return (
            "Push git commits to remote repository. "
            "Optionally specify remote name and branch. "
            "Supports setting upstream for new branches."
        )

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Remote name (default: origin)",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name to push (default: current branch)",
                },
                "set_upstream": {
                    "type": "boolean",
                    "description": "Whether to set upstreamstream (default: false)",
                },
            },
            "required": [],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the git push command.

        Args:
            **kwargs: Optional 'remote', 'branch', and 'set_upstream' parameters.

        Returns:
            ToolResult with push output or error.
        """
        try:
            remote = kwargs.get("remote", "origin")
            branch = kwargs.get("branch")
            set_upstream = kwargs.get("set_upstream", False)

            # Get current branch if not specified
            if not branch:
                branch_result = self._git_tools._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
                if not branch_result.success:
                    return branch_result
                branch = branch_result.output.strip()

            # Build git push command
            args = ["push"]
            if set_upstream:
                args.append("-u")
            args.extend([remote, branch])

            return self._git_tools._run_git(args)

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitPullRequestTool(Tool):
    """Tool for creating pull requests via Git hosting platforms."""

    def __init__(self, workspace_root: str = ".", timeout: int = 300) -> None:
        """Initialize the git pull request tool.

        Args:
            workspace_root: Working directory for Git operations.
            timeout: Timeout for Git operation in seconds.
        """
        self._git_tools = GitTools(workspace_root, timeout)

    @property
    def name(self) -> str:
        """Return tool name."""
        return "git_pull_request"

    @property
    def description(self) -> str:
        """Return tool description."""
        return (
            "Create a pull request on GitHub, GitLab, or other Git hosting platforms. "
            "Uses the 'gh' CLI for GitHub, 'glab' for GitLab, or falls back to showing instructions. "
            "Requires appropriate CLI tool to be installed and authenticated."
        )

    @property
    def schema(self) -> dict:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Pull request title",
                },
                "body": {
                    "type": "string",
                    "description": "Pull request description/body (optional)",
                },
                "base": {
                    "type": "string",
                    "description": "Base branch to merge into (default: main or master)",
                },
                "head": {
                    "type": "string",
                    "description": "Head branch to merge from (default: current branch)",
                },
                "draft": {
                    "type": "boolean",
                    "description": "Whether to create as draft PR (default: false)",
                },
                "platform": {
                    "type": "string",
                    "description": "Git platform: 'github', 'gitlab', or 'auto' (default: auto)",
                    "enum": ["github", "gitlab", "auto"],
                },
            },
            "required": ["title"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the pull request creation command.

        Args:
            **kwargs: Must contain 'title', optional 'body', 'base', 'head', 'draft', 'platform'.

        Returns:
            ToolResult with PR creation output or error.
        """
        try:
            title = kwargs.get("title")
            body = kwargs.get("body", "")
            base = kwargs.get("base")
            head = kwargs.get("head")
            draft = kwargs.get("draft", False)
            platform = kwargs.get("platform", "auto")

            if not title:
                return ToolResult(success=False, error="Missing required parameter: title")

            # Auto-detect platform if needed
            if platform == "auto":
                # Try to detect GitHub first
                gh_check = self._git_tools._run_git(["config", "--get", "remote.origin.url"])
                if gh_check.success and "github.com" in gh_check.output:
                    platform = "github"
                elif gh_check.success and "gitlab.com" in gh_check.output:
                    platform = "gitlab"
                else:
                    platform = "github"  # Default to GitHub

            # Get current branch if head not specified
            if not head:
                branch_result = self._git_tools._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
                if not branch_result.success:
                    return branch_result
                head = branch_result.output.strip()

            # Auto-detect base branch if not specified
            if not base:
                detect_result = self._git_tools._run_git(["branch", "--list", "main"])
                if detect_result.success and detect_result.output.strip():
                    base = "main"
                else:
                    base = "master"

            # Create PR based on platform
            if platform == "github":
                return self._create_github_pr(title, body, base, head, draft)
            elif platform == "gitlab":
                return self._create_gitlab_mr(title, body, base, head, draft)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported platform: {platform}. Use 'github' or 'gitlab'.",
                )

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _create_github_pr(
        self, title: str, body: str, base: str, head: str, draft: bool
    ) -> ToolResult:
        """Create a GitHub pull request using gh CLI."""
        args = ["pr", "create", "--title", title, "--base", base, "--head", head]

        if body:
            args.extend(["--body", body])

        if draft:
            args.append("--draft")

        # Check if gh CLI is available
        check_result = subprocess.run(
            ["which", "gh"],
            shell=False,
            capture_output=True,
            text=True,
        )

        if check_result.returncode != 0:
            return ToolResult(
                success=False,
                error=(
                    "GitHub CLI (gh) not found. Please install it from https://cli.github.com/ "
                    "or authenticate with 'gh auth login'"
                ),
            )

        return self._git_tools._run_git(args)

    def _create_gitlab_mr(
        self, title: str, body: str, base: str, head: str, draft: bool
    ) -> ToolResult:
        """Create a GitLab merge request using glab CLI."""
        args = ["mr", "create", "--title", title, "--target-branch", base, "--source-branch", head]

        if body:
            args.extend(["--description", body])

        if draft:
            args.append("--draft")

        # Check if glab CLI is available
        check_result = subprocess.run(
            ["which", "glab"],
            shell=False,
            capture_output=True,
            text=True,
        )

        if check_result.returncode != 0:
            return ToolResult(
                success=False,
                error=(
                    "GitLab CLI (glab) not found. Please install it from https://gitlab.com/gitlab-org/cli "
                    "or authenticate with 'glab auth login'"
                ),
            )

        return self._git_tools._run_git(args)
