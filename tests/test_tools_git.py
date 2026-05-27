"""Tests for the Git tools."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from coding_agent.tools.git import (
    GitCommitTool,
    GitDiffTool,
    GitPullRequestTool,
    GitPushTool,
    GitTools,
)
from coding_agent.tools.base import ToolResult


class TestGitTools:
    """Tests for the GitTools helper class."""

    def test_init_default_values(self):
        """Test GitTools initialization with default values."""
        git_tools = GitTools()
        assert git_tools.workspace_root == "."
        assert git_tools.timeout == 300

    def test_init_custom_values(self):
        """Test GitTools initialization with custom values."""
        git_tools = GitTools(workspace_root="/test/path", timeout=60)
        assert git_tools.workspace_root == "/test/path"
        assert git_tools.timeout == 60

    @patch("coding_agent.tools.git.subprocess.run")
    def test_run_git_success(self, mock_run):
        """Test running a successful Git command."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "status"],
            returncode=0,
            stdout="On branch main\n",
            stderr="",
        )

        git_tools = GitTools()
        result = git_tools._run_git(["status"])

        assert result.success is True
        assert "On branch main" in result.output
        assert result.error is None
        mock_run.assert_called_once()

    @patch("coding_agent.tools.git.subprocess.run")
    def test_run_git_failure(self, mock_run):
        """Test running a failed Git command."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "checkout", "nonexistent"],
            returncode=1,
            stdout="",
            stderr="error: pathspec 'nonexistent' did not match any file(s)",
        )

        git_tools = GitTools()
        result = git_tools._run_git(["checkout", "nonexistent"])

        assert result.success is False
        assert result.error is not None
        assert "failed with code 1" in result.error
        assert "STDERR:" in result.output

    @patch("coding_agent.tools.git.subprocess.run")
    def test_run_git_with_stderr(self, mock_run):
        """Test running a Git command that produces stderr output."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "push"],
            returncode=0,
            stdout="",
            stderr="Enumerating objects: 5, done.\nCounting objects: 100% (5/5), done.",
        )

        git_tools = GitTools()
        result = git_tools._run_git(["push"])

        assert result.success is True
        assert "STDERR:" in result.output
        assert "Enumerating objects" in result.output

    @patch("coding_agent.tools.git.subprocess.run")
    def test_run_git_timeout(self, mock_run):
        """Test Git command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["git", "fetch"], timeout=300)

        git_tools = GitTools(timeout=300)
        result = git_tools._run_git(["fetch"])

        assert result.success is False
        assert "timed out after 300s" in result.error

    @patch("coding_agent.tools.git.subprocess.run")
    def test_run_git_exception(self, mock_run):
        """Test Git command exception handling."""
        mock_run.side_effect = Exception("Git not found")

        git_tools = GitTools()
        result = git_tools._run_git(["status"])

        assert result.success is False
        assert result.error == "Git not found"

    @patch("coding_agent.tools.git.subprocess.run")
    def test_run_git_no_output(self, mock_run):
        """Test Git command with no output."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "add", "."],
            returncode=0,
            stdout="",
            stderr="",
        )

        git_tools = GitTools()
        result = git_tools._run_git(["add", "."])

        assert result.success is True
        assert "(no output)" in result.output


class TestGitDiffTool:
    """Tests for the GitDiffTool class."""

    def test_tool_properties(self):
        """Test GitDiffTool properties."""
        tool = GitDiffTool()
        assert tool.name == "git_diff"
        assert "diff" in tool.description.lower()
        assert isinstance(tool.schema, dict)

    def test_schema_structure(self):
        """Test GitDiffTool schema structure."""
        tool = GitDiffTool()
        schema = tool.schema
        assert schema["type"] == "object"
        assert "base_branch" in schema["properties"]
        assert "cached" in schema["properties"]
        assert schema["required"] == []

    @patch.object(GitTools, "_run_git")
    def test_execute_auto_detect_main(self, mock_run_git):
        """Test git diff with auto-detection of main branch."""
        # First call detects main branch exists
        mock_run_git.side_effect = [
            ToolResult(success=True, output="* main\n"),  # Detect main
            ToolResult(success=True, output="diff output"),  # Run diff
        ]

        tool = GitDiffTool()
        result = tool.execute()

        assert result.success is True
        assert mock_run_git.call_count == 2
        # Verify it used main as base branch
        calls = mock_run_git.call_args_list
        assert ["branch", "--list", "main"] in [call[0][0] for call in calls]

    @patch.object(GitTools, "_run_git")
    def test_execute_auto_detect_master(self, mock_run_git):
        """Test git diff with auto-detection of master branch when main doesn't exist."""
        # First call shows main doesn't exist
        mock_run_git.side_effect = [
            ToolResult(success=True, output=""),  # No main branch
            ToolResult(success=True, output="diff output"),  # Run diff
        ]

        tool = GitDiffTool()
        result = tool.execute()

        assert result.success is True
        assert mock_run_git.call_count == 2

    @patch.object(GitTools, "_run_git")
    def test_execute_explicit_base_branch(self, mock_run_git):
        """Test git diff with explicitly specified base branch."""
        mock_run_git.return_value = ToolResult(success=True, output="diff output")

        tool = GitDiffTool()
        result = tool.execute(base_branch="develop")

        assert result.success is True
        mock_run_git.assert_called_once()
        # Verify it used the specified branch
        call_args = mock_run_git.call_args[0][0]
        assert "develop" in call_args

    @patch.object(GitTools, "_run_git")
    def test_execute_cached_changes(self, mock_run_git):
        """Test git diff showing only staged changes."""
        mock_run_git.return_value = ToolResult(success=True, output="staged diff")

        tool = GitDiffTool()
        result = tool.execute(cached=True)

        assert result.success is True
        call_args = mock_run_git.call_args[0][0]
        assert "--cached" in call_args

    @patch.object(GitTools, "_run_git")
    def test_execute_failure(self, mock_run_git):
        """Test git diff failure handling."""
        mock_run_git.return_value = ToolResult(
            success=False, error="Git command failed with code 128"
        )

        tool = GitDiffTool()
        result = tool.execute()

        assert result.success is False
        assert result.error is not None

    @patch.object(GitTools, "_run_git")
    def test_execute_exception(self, mock_run_git):
        """Test git diff exception handling."""
        mock_run_git.side_effect = Exception("Unexpected error")

        tool = GitDiffTool()
        result = tool.execute()

        assert result.success is False
        assert result.error == "Unexpected error"


class TestGitCommitTool:
    """Tests for the GitCommitTool class."""

    def test_tool_properties(self):
        """Test GitCommitTool properties."""
        tool = GitCommitTool()
        assert tool.name == "git_commit"
        assert "commit" in tool.description.lower()
        assert isinstance(tool.schema, dict)

    def test_schema_structure(self):
        """Test GitCommitTool schema structure."""
        tool = GitCommitTool()
        schema = tool.schema
        assert schema["type"] == "object"
        assert "message" in schema["properties"]
        assert "all_files" in schema["properties"]
        assert "message" in schema["required"]

    @patch.object(GitTools, "_run_git")
    def test_execute_simple_commit(self, mock_run_git):
        """Test creating a simple commit."""
        mock_run_git.return_value = ToolResult(
            success=True, output="[main abc123] Commit message"
        )

        tool = GitCommitTool()
        result = tool.execute(message="Commit message")

        assert result.success is True
        mock_run_git.assert_called_once()
        call_args = mock_run_git.call_args[0][0]
        assert "commit" in call_args
        assert "-m" in call_args
        assert "Commit message" in call_args

    @patch.object(GitTools, "_run_git")
    def test_execute_commit_with_all_files(self, mock_run_git):
        """Test creating a commit with all files staged."""
        mock_run_git.side_effect = [
            ToolResult(success=True, output=""),  # Stage files
            ToolResult(success=True, output="[main abc123] Commit message"),  # Commit
        ]

        tool = GitCommitTool()
        result = tool.execute(message="Commit message", all_files=True)

        assert result.success is True
        assert mock_run_git.call_count == 2
        # First call should be add -A
        first_call_args = mock_run_git.call_args_list[0][0][0]
        assert "add" in first_call_args
        assert "-A" in first_call_args

    @patch.object(GitTools, "_run_git")
    def test_execute_commit_staging_failure(self, mock_run_git):
        """Test commit failure when staging fails."""
        mock_run_git.side_effect = [
            ToolResult(success=False, error="Failed to stage"),  # Stage files fails
        ]

        tool = GitCommitTool()
        result = tool.execute(message="Commit message", all_files=True)

        assert result.success is False
        assert result.error == "Failed to stage"

    def test_execute_missing_message(self):
        """Test commit with missing message parameter."""
        tool = GitCommitTool()
        result = tool.execute()

        assert result.success is False
        assert "Missing required parameter: message" in result.error

    @patch.object(GitTools, "_run_git")
    def test_execute_commit_failure(self, mock_run_git):
        """Test commit failure handling."""
        mock_run_git.return_value = ToolResult(
            success=False, error="Git command failed with code 1"
        )

        tool = GitCommitTool()
        result = tool.execute(message="Commit message")

        assert result.success is False
        assert result.error is not None

    @patch.object(GitTools, "_run_git")
    def test_execute_exception(self, mock_run_git):
        """Test commit exception handling."""
        mock_run_git.side_effect = Exception("Unexpected error")

        tool = GitCommitTool()
        result = tool.execute(message="Commit message")

        assert result.success is False
        assert result.error == "Unexpected error"


class TestGitPushTool:
    """Tests for the GitPushTool class."""

    def test_tool_properties(self):
        """Test GitPushTool properties."""
        tool = GitPushTool()
        assert tool.name == "git_push"
        assert "push" in tool.description.lower()
        assert isinstance(tool.schema, dict)

    def test_schema_structure(self):
        """Test GitPushTool schema structure."""
        tool = GitPushTool()
        schema = tool.schema
        assert schema["type"] == "object"
        assert "remote" in schema["properties"]
        assert "branch" in schema["properties"]
        assert "set_upstream" in schema["properties"]
        assert schema["required"] == []

    @patch.object(GitTools, "_run_git")
    def test_execute_default_push(self, mock_run_git):
        """Test pushing to default remote and current branch."""
        mock_run_git.side_effect = [
            ToolResult(success=True, output="main"),  # Get current branch
            ToolResult(success=True, output="Everything up-to-date"),  # Push
        ]

        tool = GitPushTool()
        result = tool.execute()

        assert result.success is True
        assert mock_run_git.call_count == 2
        # Second call should be push
        second_call_args = mock_run_git.call_args_list[1][0][0]
        assert "push" in second_call_args
        assert "origin" in second_call_args
        assert "main" in second_call_args

    @patch.object(GitTools, "_run_git")
    def test_execute_custom_remote_and_branch(self, mock_run_git):
        """Test pushing to custom remote and branch."""
        mock_run_git.return_value = ToolResult(
            success=True, output="Enumerating objects... done."
        )

        tool = GitPushTool()
        result = tool.execute(remote="upstream", branch="feature")

        assert result.success is True
        call_args = mock_run_git.call_args[0][0]
        assert "push" in call_args
        assert "upstream" in call_args
        assert "feature" in call_args

    @patch.object(GitTools, "_run_git")
    def test_execute_with_set_upstream(self, mock_run_git):
        """Test pushing with set upstream flag."""
        mock_run_git.return_value = ToolResult(
            success=True, output="Branch 'feature' set up to track 'origin/feature'"
        )

        tool = GitPushTool()
        result = tool.execute(branch="feature", set_upstream=True)

        assert result.success is True
        call_args = mock_run_git.call_args[0][0]
        assert "-u" in call_args

    @patch.object(GitTools, "_run_git")
    def test_execute_branch_detection_failure(self, mock_run_git):
        """Test push failure when branch detection fails."""
        mock_run_git.return_value = ToolResult(
            success=False, error="fatal: not a git repository"
        )

        tool = GitPushTool()
        result = tool.execute()

        assert result.success is False
        assert result.error is not None

    @patch.object(GitTools, "_run_git")
    def test_execute_push_failure(self, mock_run_git):
        """Test push failure handling."""
        mock_run_git.side_effect = [
            ToolResult(success=True, output="main"),  # Get current branch
            ToolResult(
                success=False, error="rejected non-fast-forward"
            ),  # Push fails
        ]

        tool = GitPushTool()
        result = tool.execute()

        assert result.success is False
        assert result.error is not None

    @patch.object(GitTools, "_run_git")
    def test_execute_exception(self, mock_run_git):
        """Test push exception handling."""
        mock_run_git.side_effect = Exception("Unexpected error")

        tool = GitPushTool()
        result = tool.execute()

        assert result.success is False
        assert result.error == "Unexpected error"


class TestGitPullRequestTool:
    """Tests for the GitPullRequestTool class."""

    def test_tool_properties(self):
        """Test GitPullRequestTool properties."""
        tool = GitPullRequestTool()
        assert tool.name == "git_pull_request"
        assert "pull request" in tool.description.lower()
        assert isinstance(tool.schema, dict)

    def test_schema_structure(self):
        """Test GitPullRequestTool schema structure."""
        tool = GitPullRequestTool()
        schema = tool.schema
        assert schema["type"] == "object"
        assert "title" in schema["properties"]
        assert "body" in schema["properties"]
        assert "base" in schema["properties"]
        assert "head" in schema["properties"]
        assert "draft" in schema["properties"]
        assert "platform" in schema["properties"]
        assert "title" in schema["required"]
        assert schema["properties"]["platform"]["enum"] == ["github", "gitlab", "auto"]

    def test_execute_missing_title(self):
        """Test PR creation with missing title parameter."""
        tool = GitPullRequestTool()
        result = tool.execute()

        assert result.success is False
        assert "Missing required parameter: title" in result.error

    @patch.object(GitTools, "_run_git")
    @patch("subprocess.run")
    def test_execute_github_pr_success(self, mock_subprocess_run, mock_run_git):
        """Test successful GitHub PR creation."""
        # Setup mocks
        mock_run_git.side_effect = [
            ToolResult(success=True, output="https://github.com/user/repo.git"),  # Detect platform
            ToolResult(success=True, output="feature-branch"),  # Get current branch
            ToolResult(success=True, output="* main\n"),  # Detect main branch
            ToolResult(success=True, output="PR created successfully"),  # Create PR
        ]
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=["which", "gh"], returncode=0, stdout="/usr/bin/gh", stderr=""
        )

        tool = GitPullRequestTool()
        result = tool.execute(
            title="Add new feature",
            body="This PR adds a new feature",
            draft=False,
        )

        assert result.success is True
        # Should have called git multiple times
        assert mock_run_git.call_count >= 3

    @patch.object(GitTools, "_run_git")
    @patch("subprocess.run")
    def test_execute_github_pr_draft(self, mock_subprocess_run, mock_run_git):
        """Test creating a draft GitHub PR."""
        mock_run_git.side_effect = [
            ToolResult(success=True, output="https://github.com/user/repo.git"),
            ToolResult(success=True, output="feature-branch"),
            ToolResult(success=True, output="* main\n"),
            ToolResult(success=True, output="Draft PR created"),
        ]
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=["which", "gh"], returncode=0, stdout="/usr/bin/gh", stderr=""
        )

        tool = GitPullRequestTool()
        result = tool.execute(title="Draft Feature", draft=True)

        assert result.success is True

    @patch.object(GitTools, "_run_git")
    @patch("subprocess.run")
    def test_execute_github_cli_not_found(self, mock_subprocess_run, mock_run_git):
        """Test PR creation when GitHub CLI is not installed."""
        mock_run_git.side_effect = [
            ToolResult(success=True, output="https://github.com/user/repo.git"),
            ToolResult(success=True, output="feature-branch"),
            ToolResult(success=True, output="* main\n"),
        ]
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=["which", "gh"], returncode=1, stdout="", stderr=""
        )

        tool = GitPullRequestTool()
        result = tool.execute(title="Add feature")

        assert result.success is False
        assert "GitHub CLI (gh) not found" in result.error

    @patch.object(GitTools, "_run_git")
    @patch("subprocess.run")
    def test_execute_gitlab_mr_success(self, mock_subprocess_run, mock_run_git):
        """Test successful GitLab MR creation."""
        mock_run_git.side_effect = [
            ToolResult(success=True, output="https://gitlab.com/user/repo.git"),
            ToolResult(success=True, output="feature-branch"),
            ToolResult(success=True, output="* main\n"),
            ToolResult(success=True, output="MR created successfully"),
        ]
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=["which", "glab"], returncode=0, stdout="/usr/bin/glab", stderr=""
        )

        tool = GitPullRequestTool()
        result = tool.execute(
            title="Add new feature",
            body="This MR adds a new feature",
            platform="gitlab",
        )

        assert result.success is True

    @patch.object(GitTools, "_run_git")
    @patch("subprocess.run")
    def test_execute_gitlab_cli_not_found(self, mock_subprocess_run, mock_run_git):
        """Test MR creation when GitLab CLI is not installed."""
        mock_run_git.side_effect = [
            ToolResult(success=True, output="https://gitlab.com/user/repo.git"),
            ToolResult(success=True, output="feature-branch"),
            ToolResult(success=True, output="* main\n"),
        ]
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=["which", "glab"], returncode=1, stdout="", stderr=""
        )

        tool = GitPullRequestTool()
        result = tool.execute(title="Add feature", platform="gitlab")

        assert result.success is False
        assert "GitLab CLI (glab) not found" in result.error

    @patch.object(GitTools, "_run_git")
    def test_execute_unsupported_platform(self, mock_run_git):
        """Test PR creation with unsupported platform."""
        mock_run_git.side_effect = [
            ToolResult(success=True, output="https://example.com/repo.git"),
            ToolResult(success=True, output="feature-branch"),
            ToolResult(success=True, output="* main\n"),
        ]

        tool = GitPullRequestTool()
        result = tool.execute(title="Add feature", platform="bitbucket")

        assert result.success is False
        assert "Unsupported platform" in result.error

    @patch.object(GitTools, "_run_git")
    @patch("subprocess.run")
    def test_execute_auto_detect_platform(self, mock_subprocess_run, mock_run_git):
        """Test automatic platform detection."""
        mock_run_git.side_effect = [
            ToolResult(success=True, output="https://github.com/user/repo.git"),
            ToolResult(success=True, output="feature-branch"),
            ToolResult(success=True, output="* main\n"),
            ToolResult(success=True, output="PR created"),
        ]
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=["which", "gh"], returncode=0, stdout="/usr/bin/gh", stderr=""
        )

        tool = GitPullRequestTool()
        result = tool.execute(title="Auto detect platform", platform="auto")

        assert result.success is True

    @patch.object(GitTools, "_run_git")
    def test_execute_branch_detection_failure(self, mock_run_git):
        """Test PR creation failure when branch detection fails."""
        mock_run_git.return_value = ToolResult(
            success=False, error="fatal: not a git repository"
        )

        tool = GitPullRequestTool()
        result = tool.execute(title="Add feature")

        assert result.success is False

    @patch.object(GitTools, "_run_git")
    @patch("subprocess.run")
    def test_execute_exception(self, mock_subprocess_run, mock_run_git):
        """Test PR creation exception handling."""
        mock_run_git.side_effect = Exception("Unexpected error")

        tool = GitPullRequestTool()
        result = tool.execute(title="Add feature")

        assert result.success is False
        assert result.error == "Unexpected error"


class TestGitToolsIntegration:
    """Integration tests for Git tools working together."""

    @patch.object(GitTools, "_run_git")
    def test_workflow_diff_commit_push(self, mock_run_git):
        """Test a typical workflow: diff, commit, and push."""
        # Setup mock responses for the workflow
        mock_run_git.side_effect = [
            ToolResult(success=True, output="* main\n"),  # Diff: detect main
            ToolResult(success=True, output="diff output"),  # Diff: show changes
            ToolResult(success=True, output=""),  # Commit: stage files
            ToolResult(success=True, output="[main abc123] Add feature"),  # Commit
            ToolResult(success=True, output="main"),  # Push: get branch
            ToolResult(success=True, output="Everything up-to-date"),  # Push
        ]

        # Execute workflow
        diff_tool = GitDiffTool()
        diff_result = diff_tool.execute()
        assert diff_result.success is True

        commit_tool = GitCommitTool()
        commit_result = commit_tool.execute(message="Add feature", all_files=True)
        assert commit_result.success is True

        push_tool = GitPushTool()
        push_result = push_tool.execute()
        assert push_result.success is True

        # Verify all calls were made
        assert mock_run_git.call_count == 6
