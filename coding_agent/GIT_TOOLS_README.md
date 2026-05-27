# Git Operations Tools

This document describes the Git operations tools available in the Coding Agent.

## Overview

The Git tools provide a comprehensive set of capabilities for version control operations, including:

- Checking differences between branches
- Creating commits
- Pushing changes to remote repositories
- Creating pull requests on GitHub or GitLab

## Available Tools

### 1. GitDiffTool (`git_diff`)

Check git diff between current branch and main/master branch.

**Description:** Shows all changes made in the current branch compared to the base branch. Automatically detects whether to use 'main' or 'master' as the base branch.

**Parameters:**
- `base_branch` (string, optional): Base branch to compare against. Auto-detects main/master if not specified.
- `cached` (boolean, optional): Whether to show staged changes only. Default: false.

**Example Usage:**
```python
from coding_agent.tools import GitDiffTool

# Basic usage - auto-detects main/master
tool = GitDiffTool()
result = tool.execute()

# Specify base branch
result = tool.execute(base_branch="develop")

# Show only staged changes
result = tool.execute(cached=True)
```

### 2. GitCommitTool (`git_commit`)

Create a git commit with the specified message.

**Description:** Creates a git commit with support for conventional commit format. Optionally stages all changes before committing.

**Parameters:**
- `message` (string, required): Commit message.
- `all_files` (boolean, optional): Whether to stage all changed files before committing. Default: false.

**Example Usage:**
```python
from coding_agent.tools import GitCommitTool

# Create a simple commit
tool = GitCommitTool()
result = tool.execute(message="feat: add new feature")

# Stage all files and commit
result = tool.execute(message="fix: resolve bug in authentication", all_files=True)
```

### 3. GitPushTool (`git_push`)

Push git commits to remote repository.

**Description:** Pushes git commits to remote repository with support for setting upstream for new branches.

**Parameters:**
- `remote` (string, optional): Remote name. Default: "origin".
- `branch` (string, optional): Branch name to push. Default: current branch.
- `set_upstream` (boolean, optional): Whether to set upstream. Default: false.

**Example Usage:**
```python
from coding_agent.tools import GitPushTool

# Push to origin with current branch
tool = GitPushTool()
result = tool.execute()

# Push with upstream
result = tool.execute(set_upstream=True)

# Specify remote and branch
result = tool.execute(remote="upstream", branch="feature-branch")
```

### 4. GitPullRequestTool (`git_pull_request`)

Create a pull request on GitHub or GitLab.

**Description:** Creates a pull request on GitHub (using `gh` CLI) or GitLab (using `glab` CLI). Requires the appropriate CLI tool to be installed and authenticated.

**Parameters:**
- `title` (string, required): Pull request title.
- `body` (string, optional): Pull request description/body.
- `base` (string, optional): Base branch to merge into. Default: main or master.
- `head` (string, optional): Head branch to merge from. Default: current branch.
- `draft` (boolean, optional): Whether to create as draft PR. Default: false.
- `platform` (string, optional): Git platform: 'github', 'gitlab', or 'auto'. Default: 'auto'.

**Prerequisites:**
- For GitHub: Install [GitHub CLI](https://cli.github.com/) and authenticate with `gh auth login`
- For GitLab: Install [GitLab CLI](https://gitlab.com/gitlab-org/cli) and authenticate with `glab auth login`

**Example Usage:**
```python
from coding_agent.tools import GitPullRequestTool

# Create a basic PR (auto-detects platform)
tool = GitPullRequestTool()
result = tool.execute(
    title="Add new feature",
    body="This PR adds the new feature described in issue #123"
)

# Create a draft PR on GitHub
result = tool.execute(
    title="WIP: New authentication system",
    body="Work in progress - do not merge yet",
    draft=True,
    platform="github"
)

# Specify base and head branches
result = tool.execute(
    title="Merge feature into develop",
    base="develop",
    head="feature/new-auth"
)
```

## Installation Requirements

For full Git functionality, ensure you have:

1. **Git** installed and configured
2. **GitHub CLI** (for GitHub PRs): 
   ```bash
   # Install gh CLI
   brew install gh  # macOS
   sudo apt install gh  # Linux
   
   # Authenticate
   gh auth login
   ```

3. **GitLab CLI** (for GitLab MRs):
   ```bash
   # Install glab CLI
   brew install glab  # macOS
   sudo apt install glab  # Linux
   
   # Authenticate
   glab auth login
   ```

## Security Considerations

All Git operations are executed within the configured `workspace_root` directory to prevent unauthorized access to repositories outside the project scope. The tools use subprocess with `shell=False` to prevent shell injection vulnerabilities.

## Error Handling

All Git tools return a `ToolResult` object with:
- `success`: Boolean indicating if the operation succeeded
- `output`: String containing the command output
- `error`: Optional error message if execution failed

Example error handling:
```python
from coding_agent.tools import GitCommitTool

tool = GitCommitTool()
result = tool.execute(message="feat: add feature")

if result.success:
    print(f"Commit successful: {result.output}")
else:
    print(f"Commit failed: {result.error}")
```

## Integration with LLM

These tools are automatically available to the LLM when registered with the agent's tool registry. The LLM can use them to:

1. Check what changes have been made (`git_diff`)
2. Commit changes after completing tasks (`git_commit`)
3. Push commits to remote (`git_push`)
4. Create pull requests for code review (`git_pull_request`)

Example LLM workflow:
```python
from coding_agent.core import CodingAgent
from coding_agent.tools import GitDiffTool, GitCommitTool, GitPushTool

agent = CodingAgent(...)
agent.register_tool(GitDiffTool())
agent.register_tool(GitCommitTool())
agent.register_tool(GitPushTool())

# LLM can now use these tools autonomously
response = agent.run("Check what changes I've made, commit them, and push to remote")
```

## Troubleshooting

### Common Issues

1. **"Git command failed"** - Ensure you're in a valid Git repository
2. **"gh CLI not found"** - Install GitHub CLI from https://cli.github.com/
3. **"glab CLI not found"** - Install GitLab CLI from https://gitlab.com/gitlab-org/cli
4. **"Authentication failed"** - Run `gh auth login` or `glab auth login`
5. **"No remote configured"** - Add a remote with `git remote add origin <url>`

### Debugging Tips

Enable verbose output by checking the raw output:
```python
result = tool.execute(...)
print(f"Output: {result.output}")
print(f"Error: {result.error}")
```
