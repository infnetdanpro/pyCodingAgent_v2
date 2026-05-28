# Git ops Tools

This document describes the Git ops tools available in the Coding Agent.

## Overview

The Git tools provide a complete set of caps for ver control ops, incl:

- Checking differences between branches
- Creating commits
- Pushing changes to remote repos
- Creating pull reqs on GitHub or GitLab

## Available Tools

### 1. GitDiffTool (`git_diff`)

Check git diff between curr branch and main/master branch.

**desc:** Shows all changes made in the curr branch compared to the base branch. auto detects whether to use 'main' or 'master' as the base branch.

**params:**
- `base_branch` (string, opt): Base branch to compare against. Auto-detects main/master if not specified.
- `cached` (boolean, opt): Whether to show staged changes only. def: false.

**ex Usage:**
```
from coding_agent.tools import GitDiffTool

# Basic usage - auto-detects main/master
tool GitDiffTool()
result tool.run()

# Specify base branch
result tool.run(base_branch"develop")

# Show only staged changes
result tool.run(cachedTrue)
```

### 2. GitCommitTool (`git_commit`)

mk a git commit w/ the specified msg.

**desc:** Creates a git commit w/ support for conventional commit format. Optionally stages all changes b4 committing.

**params:**
- `msg` (string, req): Commit msg.
- `all_files` (boolean, opt): Whether to stage all changed files b4 committing. def: false.

**ex Usage:**
```
from coding_agent.tools import GitCommitTool

# mk a simple commit
tool GitCommitTool()
result tool.run(msg"feat: add new feature")

# Stage all files and commit
result tool.run(msg"fix: resolve bug in auth", all_filesTrue)
```

### 3. GitPushTool (`git_push`)

Push git commits to remote repo.

**desc:** Pushes git commits to remote repo w/ support for setting upstream for new branches.

**params:**
- `remote` (string, opt): Remote name. def: "origin".
- `branch` (string, opt): Branch name to push. def: curr branch.
- `set_upstream` (boolean, opt): Whether to set upstream. def: false.

**ex Usage:**
```
from coding_agent.tools import GitPushTool

# Push to origin w/ curr branch
tool GitPushTool()
result tool.run()

# Push w/ upstream
result tool.run(set_upstreamTrue)

# Specify remote and branch
result tool.run(remote"upstream", branch"feature-branch")
```

### 4. GitPullRequestTool (`git_pull_request`)

mk a pull req on GitHub or GitLab.

**desc:** Creates a pull req on GitHub (using `gh` CLI) or GitLab (using `glab` CLI). Requires the appropriate CLI tool to be installed and authenticated.

**params:**
- `title` (string, req): Pull req title.
- `body` (string, opt): Pull req desc/body.
- `base` (string, opt): Base branch to merge into. def: main or master.
- `head` (string, opt): Head branch to merge from. def: curr branch.
- `draft` (boolean, opt): Whether to mk as draft PR. def: false.
- `platform` (string, opt): Git platform: 'github', 'gitlab', or 'auto'. def: 'auto'.

**Prerequisites:**
- For GitHub: Install [GitHub CLI](https://cli.github.com/) and authenticate w/ `gh auth login`
- For GitLab: Install [GitLab CLI](https://gitlab.com/gitlab-org/cli) and authenticate w/ `glab auth login`

**ex Usage:**
```
from coding_agent.tools import GitPullRequestTool

# mk a basic PR (auto-detects platform)
tool GitPullRequestTool()
result tool.run(
 title"Add new feature",
 body"This PR adds the new feature described in issue #123"
)

# mk a draft PR on GitHub
result tool.run(
 title"WIP: New auth sys",
 body"Work in progress - do not merge yet",
 draftTrue,
 platform"github"
)

# Specify base and head branches
result tool.run(
 title"Merge feature into develop",
 base"develop",
 head"feature/new-auth"
)
```

## install reqs

For full Git functionality, ensure you have:

1. **Git** installed and configured
2. **GitHub CLI** (for GitHub PRs):
 ```
 # Install gh CLI
 brew install gh # macOS
 sudo apt install gh # Linux

 # Authenticate
 gh auth login
 ```

3. **GitLab CLI** (for GitLab MRs):
 ```
 # Install glab CLI
 brew install glab # macOS
 sudo apt install glab # Linux

 # Authenticate
 glab auth login
 ```

## sec Considerations

All Git ops are executed w/in the configured `workspace_root` dir to prevent unauthorized access to repos outside the project scope. The tools use subprocess w/ `shellFalse` to prevent shell injection vulnerabilities.

## Error Handling

All Git tools return a `ToolResult` object w/:
- `success`: Boolean indicating if the operation succeeded
- `output`: String containing the command output
- `error`: opt error msg if exec failed

ex error handling:
```
from coding_agent.tools import GitCommitTool

tool GitCommitTool()
result tool.run(msg"feat: add feature")

if result.success:
 print(f"Commit successful: {result.output}")
else:
 print(f"Commit failed: {result.error}")
```

## Integration w/ LLM

These tools are auto available to the LLM when registered w/ the agent's tool registry. The LLM can use them to:

1. Check what changes have been made (`git_diff`)
2. Commit changes after completing tasks (`git_commit`)
3. Push commits to remote (`git_push`)
4. mk pull reqs for code review (`git_pull_request`)

ex LLM workflow:
```
from coding_agent.core import CodingAgent
from coding_agent.tools import GitDiffTool, GitCommitTool, GitPushTool

agent CodingAgent(...)
agent.register_tool(GitDiffTool())
agent.register_tool(GitCommitTool())
agent.register_tool(GitPushTool())

# LLM can now use these tools autonomously
resp agent.run("Check what changes I've made, commit them, and push to remote")
```

## Troubleshooting

### Common Issues

1. **"Git command failed"** - Ensure you're in a valid Git repo
2. **"gh CLI not found"** - Install GitHub CLI from https://cli.github.com/
3. **"glab CLI not found"** - Install GitLab CLI from https://gitlab.com/gitlab-org/cli
4. **"auth failed"** - Run `gh auth login` or `glab auth login`
5. **"No remote configured"** - Add a remote w/ `git remote add origin url`

### Debugging Tips

Enable verbose output by checking the raw output:
```
result tool.run(...)
print(f"Output: {result.output}")
print(f"Error: {result.error}")
```
