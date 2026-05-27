# 🦫 Bobert Coding Agent Project

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**A modular and scalable coding agent architecture designed for on-device execution with local LLM models**

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [CLI Usage](#-cli-usage)
  - [Plan Mode in CLI](#-plan-mode-in-cli)
  - [CLI Options Reference](#-cli-options-reference)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
  - [Plan Mode Example](#-example-7-plan-mode---structured-task-execution)
- [Plan Mode](#-plan-mode)
- [Available Tools](#-available-tools)
  - [File System Tools](#-file-system-tools)
  - [Shell & Process Tools](#-shell--process-tools)
  - [Browser Automation Tools](#-browser-automation-tools)
  - [Messaging & Integration Tools](#-messaging--integration-tools)
- [Configuration](#-configuration)
- [Creating Custom Tools](#-creating-custom-tools)
- [Design Principles](#-design-principles)
- [Requirements](#-requirements)
- [License](#-license)

---

## 🎯 Overview

The **Coding Agent** is a powerful, modular AI assistant designed to help with software development tasks. It leverages local Large Language Models (LLMs) through OpenAI-compatible APIs, enabling privacy-focused, offline-capable code generation, file manipulation, and task automation.

Built with clean architecture principles, the coding agent follows the **ReAct pattern** (Reasoning + Acting) to intelligently plan and execute complex development tasks by combining LLM reasoning with practical tool execution.

### Key Use Cases

- 📝 **Code Generation**: Write new code files or functions
- 🔍 **Code Analysis**: Read and understand existing codebases
- 🛠️ **Refactoring**: Modify and improve existing code
- 🧪 **Testing**: Execute code snippets and run tests
- 📂 **File Management**: Navigate, read, and modify project files
- 🖥️ **Automation**: Execute shell commands and scripts

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🔌 OpenAI-Compatible API** | Works seamlessly with local models like Qwen2.5-Coder via Ollama, LM Studio, or any OpenAI-compatible endpoint |
| **🧩 Modular Tool System** | Easy-to-extend architecture for adding custom tools and capabilities |
| **🔄 ReAct Pattern** | Advanced reasoning and acting loop for complex task completion |
| **💾 Conversation History** | Persistent context across sessions for continuous workflows |
| **📚 Well Documented** | Comprehensive docstrings following Google Style Guide |
| **🎨 Clean Architecture** | KISS and DRY principles for maintainable code |
| **🔒 Privacy-First** | Runs entirely locally with no external API dependencies required |
| **⚡ Type-Safe** | Full type hints throughout the codebase |

---

## 📁 Project Structure

```
/workspace/
├── coding_agent/              # Main package directory
│   ├── __init__.py           # Package initialization
│   ├── README.md             # Package-specific documentation
│   ├── requirements.txt      # Python dependencies
│   │
│   ├── config/               # Configuration modules
│   │   ├── __init__.py
│   │   ├── settings.py       # Agent settings and configuration
│   │   └── model_config.py   # LLM model configuration
│   │
│   ├── core/                 # Core agent logic
│   │   ├── __init__.py
│   │   ├── agent.py          # Main CodingAgent class
│   │   └── context.py        # Conversation context management
│   │
│   ├── llm/                  # LLM client implementation
│   │   ├── __init__.py
│   │   ├── client.py         # OpenAI-compatible client
│   │   └── message.py        # Message and role definitions
│   │
│   ├── tools/                # Tool implementations
│   │   ├── __init__.py
│   │   ├── base.py           # Base tool classes and registry
│   │   ├── filesystem.py     # File system operations
│   │   └── shell.py          # Shell command execution
│   │
│   ├── utils/                # Utility functions
│   │   ├── __init__.py
│   │   └── logging_config.py # Logging setup
│   │
│   └── examples/             # Usage examples
│       ├── basic_usage.py    # Interactive agent example
│       └── custom_tools.py   # Custom tool demonstration
│
└── README.md                 # This file - Project overview
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+** recommended
- **Local LLM** (optional but recommended for offline use)

### Step 1: Install from GitHub

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install directly from GitHub repository
pip install git+https://github.com/yourusername/coding-agent.git
```

### Step 2: Initialize Your Project Directory

```bash
# Initialize current directory
agent init

# Or initialize a specific directory
agent init /path/to/your/project
```

This creates:
- `.agent_config.json` - Configuration file for the agent
- `.gitignore` - Pre-configured to ignore agent history and cache files

### Step 3: Setup Local LLM (Recommended)

Install [Ollama](https://ollama.ai/) for local model inference:

```bash
# Install Ollama (Linux/Mac)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a coding-optimized model
ollama pull qwen2.5-coder:7b

# Start Ollama server (usually auto-starts)
ollama serve
```

Alternative models you can use:
- `codellama:7b` - General purpose coding model
- `deepseek-coder:6.7b` - Specialized for code generation
- `starcoder2:7b` - Multi-language code model

---

## 💻 CLI Usage

The coding agent provides a command-line interface for easy interaction.

### Initialize a Project

```bash
# Initialize current directory
agent init

# Initialize a specific directory
agent init /path/to/project
```

### Start Interactive Chat

```bash
# Start chat in current directory
agent chat

# Specify workspace directory
agent chat -w /path/to/project

# Use custom model configuration
agent chat --model codellama:7b --base-url http://localhost:11434/v1
```

### Run Single Command

```bash
# Execute a single task
agent run "List all Python files in the current directory"

# With custom workspace
agent run "Create a README.md file" -w /path/to/project
```

### CLI Commands Reference

| Command | Description |
|---------|-------------|
| `agent init [dir]` | Initialize a directory for use with the agent |
| `agent chat` | Start interactive chat session |
| `agent run "command"` | Execute a single command |

### In-Chat Commands

When using `agent chat`, you can use these special commands:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/tools` | List available tools |
| `/plan <request>` | Generate and execute a plan for your request |
| `/quit` | Exit the chat session |

### Plan Mode in CLI

The `/plan` command in interactive chat allows you to generate, review, and execute plans:

```bash
$ agent chat

> /plan Create a Flask API with user authentication

Generating plan...

Plan: Create Flask API with Authentication
  1. [☐] Create project directory structure
  2. [☐] Install Flask and dependencies
  3. [☐] Create app.py with basic Flask setup
  4. [☐] Implement user registration endpoint
  5. [☐] Implement login/logout endpoints
  6. [☐] Add password hashing with bcrypt
  7. [☐] Create database models
  8. [☐] Write basic tests

Select plan items to execute (or press Enter to execute all):
> _
```

You can then select which steps to execute by toggling them on/off before confirmation.

### Complete CLI Workflow Example

```bash
# 1. Initialize a new project directory
agent init my-flask-app
cd my-flask-app

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Start interactive chat
agent chat --model qwen2.5-coder:7b

# In the chat session:
# > Create a Flask application with a hello world endpoint
# > Add a /users endpoint that returns a list of users
# > /plan Add user authentication with JWT tokens
# > /quit

# 4. Or run a single command non-interactively
agent run "Add type hints to all functions in app.py"
```

### Advanced CLI Usage

#### Custom Model Configuration

```bash
# Use OpenAI GPT-4
agent chat \
  --base-url https://api.openai.com/v1 \
  --api-key $OPENAI_API_KEY \
  --model gpt-4-turbo-preview

# Use Anthropic Claude via proxy
agent chat \
  --base-url https://your-claude-proxy.com/v1 \
  --api-key $ANTHROPIC_API_KEY \
  --model claude-3-opus-20240229
```

#### Debugging with Verbose Logging

```bash
# Enable DEBUG logging to see detailed agent reasoning
agent chat --log-level DEBUG

# Logs will show:
# - LLM requests and responses
# - Tool execution details
# - Agent decision-making process
```

### CLI Options Reference

#### Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--base-url` | LLM API base URL | `http://localhost:11434/v1` |
| `--api-key` | LLM API key | `ollama` |
| `--model` | LLM model name | `qwen2.5-coder:7b` |
| `--log-level` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `-w, --workspace` | Workspace directory | Current directory |

#### Environment Variables

You can configure defaults using environment variables:

```bash
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_API_KEY=your-api-key
export LLM_MODEL=qwen2.5-coder:7b
```

---

## ⚡ Quick Start

### Basic Usage Example

Here's a minimal example to get started:

```python
from coding_agent.config import ModelConfig, Settings
from coding_agent.core import CodingAgent
from coding_agent.tools import ReadFileTool, WriteFileTool, ListDirTool
from coding_agent.utils import setup_logging

# Setup logging
setup_logging(level="INFO")

# Configure settings
settings = Settings(workspace_dir=".")

# Configure model connection
model_config = ModelConfig(
    base_url="http://localhost:11434/v1",  # Ollama default endpoint
    api_key="ollama",                       # Dummy key for local models
    model_name="qwen2.5-coder:7b",          # Model to use
)

# Create and run agent
with CodingAgent(settings=settings, model_config=model_config) as agent:
    # Register tools
    agent.register_tool(ReadFileTool())
    agent.register_tool(WriteFileTool())
    agent.register_tool(ListDirTool())
    
    # Run a task
    response = agent.run("List all Python files in the current directory")
    print(response)
```

### Run the Interactive Example

```bash
cd /workspace
python -m coding_agent.examples.basic_usage
```

This launches an interactive REPL where you can chat with the agent and give it tasks.

---

## 💡 Usage Examples

### Example 1: File Operations

```python
from coding_agent.core import CodingAgent
from coding_agent.tools import ReadFileTool, WriteFileTool

with CodingAgent() as agent:
    agent.register_tool(ReadFileTool())
    agent.register_tool(WriteFileTool())
    
    # Create a new file
    response = agent.run(
        "Create a new Python file called 'hello.py' that prints 'Hello, World!'"
    )
    print(response)
    
    # Read the file to verify
    response = agent.run("Read the contents of hello.py")
    print(response)
```

### Example 2: Code Analysis

```python
from coding_agent.tools import ReadFileTool, SearchFilesTool, ListDirTool

with CodingAgent() as agent:
    agent.register_tool(ReadFileTool())
    agent.register_tool(SearchFilesTool())
    agent.register_tool(ListDirTool())
    
    # Analyze project structure
    response = agent.run(
        "Find all Python files containing 'class' definition and summarize their purpose"
    )
    print(response)
```

### Example 3: Automated Testing

```python
from coding_agent.tools import RunPythonTool, WriteFileTool

with CodingAgent() as agent:
    agent.register_tool(RunPythonTool())
    agent.register_tool(WriteFileTool())
    
    # Create and test a function
    response = agent.run(
        "Create a function that calculates factorial, then test it with input 5"
    )
    print(response)
```

### Example 4: Shell Commands

```python
from coding_agent.tools import RunCommandTool

with CodingAgent() as agent:
    agent.register_tool(RunCommandTool())
    
    # Execute git commands
    response = agent.run(
        "Check git status and show the last 5 commits"
    )
    print(response)
```

### Example 5: Process Management

```python
from coding_agent.tools import StartProcessTool, ListProcessesTool, StopProcessTool

with CodingAgent() as agent:
    agent.register_tool(StartProcessTool())
    agent.register_tool(ListProcessesTool())
    agent.register_tool(StopProcessTool())
    
    # Start a web server in background
    response = agent.run(
        "Start a Python HTTP server on port 8000 in the background"
    )
    print(response)
    
    # List running processes
    response = agent.run("List all running processes")
    print(response)
    
    # Stop the server when done
    response = agent.run("Stop the HTTP server process")
    print(response)
```

### Example 6: Browser Automation

```python
from coding_agent.tools import (
    BrowserNavigateTool, 
    BrowserScreenshotTool, 
    BrowserGetContentTool
)

with CodingAgent() as agent:
    agent.register_tool(BrowserNavigateTool())
    agent.register_tool(BrowserScreenshotTool())
    agent.register_tool(BrowserGetContentTool())
    
    # Navigate and capture content
    response = agent.run(
        "Navigate to https://example.com, take a screenshot, and extract the main content"
    )
    print(response)
```

### Example 7: Plan Mode - Structured Task Execution

Plan Mode allows you to generate a detailed plan first, review and modify it, then execute the approved steps:

```python
from coding_agent.core import CodingAgent, PlanMode
from coding_agent.config import ModelConfig
from coding_agent.tools import ReadFileTool, WriteFileTool, RunCommandTool

# Setup
model_config = ModelConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model_name="qwen2.5-coder:7b"
)

with CodingAgent() as agent:
    agent.register_tool(ReadFileTool())
    agent.register_tool(WriteFileTool())
    agent.register_tool(RunCommandTool())
    
    # Initialize plan mode
    plan_mode = PlanMode(model_config)
    
    # Generate a plan for a complex task
    plan_request = "Create a Python package with setup.py, README.md, and a basic module structure"
    
    # Get system prompt and available tools
    context = agent.get_context()
    system_prompt = context.system_prompt
    available_tools = agent.tool_registry.get_all_schemas()
    
    # Generate plan
    plan = plan_mode.generate_plan(plan_request, system_prompt, available_tools)
    
    # Review the plan
    print(plan)
    # Output:
    # Plan: Create Python Package Structure
    #   1. [☐] Create directory structure: mypackage/__init__.py
    #   2. [☐] Create setup.py with package metadata
    #   3. [☐] Create README.md with project description
    #   4. [☐] Create example module file
    
    # Enable/disable specific plan items as needed
    plan_mode.toggle_plan_item(index=2)  # Disable README creation for now
    
    # Execute the enabled plan items
    enabled_items = plan.get_enabled_items()
    print(f"Executing {len(enabled_items)} steps...")
    
    # Agent will execute the enabled steps in sequence
    for item in enabled_items:
        response = agent.run(f"Execute: {item.description}")
        print(response)
        item.completed = True
    
    print("Plan execution complete!")
```

---

## 🎯 Plan Mode

Plan Mode is a powerful feature that separates planning from execution, giving you full control over complex tasks.

### How Plan Mode Works

1. **Generate Plan**: The LLM analyzes your request and creates a structured plan with discrete steps
2. **Review & Modify**: You can review each step, enable/disable specific items, or reorder them
3. **Execute**: Only the enabled steps are executed in sequence
4. **Track Progress**: Each completed step is marked, allowing you to track progress

### Benefits of Plan Mode

- **Transparency**: See exactly what the agent plans to do before it does it
- **Control**: Disable risky steps or reorganize the execution order
- **Debugging**: Easier to identify where things went wrong in a multi-step task
- **Learning**: Understand the agent's reasoning and decision-making process

### Plan Mode Architecture

The `PlanMode` class consists of:

- **`Plan`**: Container for the plan title and list of items
- **`PlanItem`**: Individual step with description, optional tool assignment, and enabled/completed status
- **`generate_plan()`**: Creates a plan from user request using LLM
- **`toggle_plan_item()`**: Enable/disable specific steps
- **`get_current_plan()`**: Retrieve the active plan

### When to Use Plan Mode

Plan Mode is especially useful for:

- Complex multi-file refactoring tasks
- Database migrations or schema changes
- Deployments with multiple steps
- Tasks requiring user approval at each stage
- Learning and understanding the agent's approach

---

## 🛠️ Available Tools

The coding agent comes with a comprehensive set of built-in tools organized into several categories:

### File System Tools

| Tool | Class | Description |
|------|-------|-------------|
| **read_file** | `ReadFileTool` | Read contents of a file with optional line range |
| **write_file** | `WriteFileTool` | Write content to a file (creates or overwrites) |
| **list_dir** | `ListDirTool` | List directory contents with file details (type, size, modified time) |
| **search_files** | `SearchFilesTool` | Search files by glob pattern (e.g., `*.py`, `**/*.md`) |
| **get_tree** | `GetTreeTool` | Get a tree view of directory structure |

### Shell & Process Tools

| Tool | Class | Description |
|------|-------|-------------|
| **run_command** | `RunCommandTool` | Execute shell commands safely within workspace |
| **run_python** | `RunPythonTool` | Execute Python code snippets in isolated environment |
| **start_process** | `StartProcessTool` | Start a long-running process in the background |
| **stop_process** | `StopProcessTool` | Stop a previously started process by PID |
| **list_processes** | `ListProcessesTool` | List all processes started by the agent |
| **get_process_info** | `GetProcessInfoTool` | Get detailed information about a specific process |

### Browser Automation Tools

| Tool | Class | Description |
|------|-------|-------------|
| **browser_navigate** | `BrowserNavigateTool` | Navigate to a URL in a headless browser |
| **browser_click** | `BrowserClickTool` | Click on an element identified by CSS selector |
| **browser_fill** | `BrowserFillTool` | Fill a form field with text |
| **browser_screenshot** | `BrowserScreenshotTool` | Take a screenshot of the current page |
| **browser_get_content** | `BrowserGetContentTool` | Extract text content from the current page |
| **browser_evaluate** | `BrowserEvaluateTool` | Execute JavaScript in the browser context |
| **browser_close** | `BrowserCloseTool` | Close the browser session |

### Messaging & Integration Tools

| Tool | Class | Description |
|------|-------|-------------|
| **slack_receive** | `SlackReceiveTool` | Receive messages from Slack channels |
| **slack_send** | `SlackSendTool` | Send messages to Slack channels |
| **telegram_receive** | `TelegramReceiveTool` | Receive messages from Telegram chats |
| **telegram_send** | `TelegramSendTool` | Send messages to Telegram chats |
| **jira_receive** | `JiraReceiveTool` | Fetch tasks/issues from Jira |
| **jira_create** | `JiraCreateTool` | Create new issues in Jira |
| **analyze_tasks** | `AnalyzeTasksTool` | Analyze and prioritize tasks from messaging platforms |

### Git Operations Tools

| Tool | Class | Description |
|------|-------|-------------|
| **git_diff** | `GitDiffTool` | Check git diff between current branch and main/master branch |
| **git_commit** | `GitCommitTool` | Create a git commit with specified message |
| **git_push** | `GitPushTool` | Push git commits to remote repository |
| **git_pull_request** | `GitPullRequestTool` | Create pull requests on GitHub or GitLab |

### Tool Security

All file system and shell tools operate within a configured `workspace_root` directory to prevent unauthorized access to sensitive files outside the project scope. Process tools track spawned processes and allow for proper cleanup.

### Tool Usage Examples

#### File Operations
```python
from coding_agent.tools import ReadFileTool, WriteFileTool, ListDirTool

# Read a specific file
tool = ReadFileTool()
result = tool.execute(path="src/main.py")

# Write a new file
tool = WriteFileTool()
result = tool.execute(path="test.py", content="print('Hello')")

# List directory with details
tool = ListDirTool()
result = tool.execute(path=".")
```

#### Process Management
```python
from coding_agent.tools import StartProcessTool, StopProcessTool

# Start a long-running server
tool = StartProcessTool()
result = tool.execute(command="python -m http.server 8000")
# Returns: {"pid": 12345, "status": "running"}

# Stop the process later
tool = StopProcessTool()
result = tool.execute(pid=12345)
```

#### Browser Automation
```python
from coding_agent.tools import BrowserNavigateTool, BrowserClickTool, BrowserScreenshotTool

# Navigate to a website
tool = BrowserNavigateTool()
result = tool.execute(url="https://example.com")

# Take a screenshot
tool = BrowserScreenshotTool()
result = tool.execute(path="screenshot.png")

# Click a button
tool = BrowserClickTool()
result = tool.execute(selector="#login-button")
```

#### Messaging Integration
```python
from coding_agent.tools import SlackSendTool, TelegramSendTool, JiraCreateTool

# Send a Slack message
tool = SlackSendTool()
result = tool.execute(
    channel="#general",
    text="Deployment complete! ✅"
)

# Send a Telegram message
tool = TelegramSendTool()
result = tool.execute(
    chat_id="123456789",
    text="Alert: Server CPU usage above 90%"
)

# Create a Jira issue
tool = JiraCreateTool()
result = tool.execute(
    project="PROJ",
    summary="Fix login bug",
    description="Users unable to login with special characters in password",
    issuetype="Bug",
    priority="High"
)
```

#### Git Operations
```python
from coding_agent.tools import GitDiffTool, GitCommitTool, GitPushTool, GitPullRequestTool

# Check git diff against main/master branch
tool = GitDiffTool()
result = tool.execute()
# Or specify base branch: result = tool.execute(base_branch="develop")

# Create a commit
tool = GitCommitTool()
result = tool.execute(message="feat: add new feature", all_files=True)

# Push to remote
tool = GitPushTool()
result = tool.execute(set_upstream=True)
# Or specify remote and branch: result = tool.execute(remote="origin", branch="feature-branch")

# Create a pull request (requires gh CLI for GitHub or glab CLI for GitLab)
tool = GitPullRequestTool()
result = tool.execute(
    title="Add new feature",
    body="This PR adds the new feature described in issue #123",
    draft=False
)
```

### Tool Architecture

All tools follow a consistent architecture:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class ToolResult:
    """Standard result structure for all tools."""
    success: bool
    output: str = ""
    error: Optional[str] = None
    data: Optional[Any] = None

class Tool(ABC):
    """Base class for all tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for LLM."""
        pass
    
    @property
    @abstractmethod
    def schema(self) -> dict:
        """JSON Schema for tool parameters."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
```

This consistent interface allows:
- Easy registration with the agent
- Automatic schema generation for LLM function calling
- Standardized error handling
- Simple testing and mocking

---

## ⚙️ Configuration

### Settings Class

Configure agent behavior with the `Settings` class:

```python
from coding_agent.config import Settings

settings = Settings(
    workspace_dir=".",              # Root directory for file operations
    max_iterations=50,              # Maximum agent loop iterations
    timeout_seconds=300,            # Tool execution timeout (seconds)
    log_level="INFO",               # Logging level: DEBUG, INFO, WARNING, ERROR
    enable_history=True,            # Persist conversation history
    history_dir=".agent_history",   # Directory for history storage
    max_context_length=128000,      # Maximum context tokens
    temperature=0.7,                # LLM temperature (creativity)
    top_p=0.95,                     # LLM nucleus sampling parameter
)
```

### ModelConfig Class

Configure LLM connection parameters:

```python
from coding_agent.config import ModelConfig

model_config = ModelConfig(
    base_url="http://localhost:11434/v1",  # API endpoint URL
    api_key="ollama",                       # API key (use actual key for cloud APIs)
    model_name="qwen2.5-coder:7b",          # Model identifier
    max_tokens=4096,                        # Maximum response tokens
    timeout=120,                            # Request timeout (seconds)
    retry_count=3,                          # Number of retry attempts
    stream=True,                            # Enable streaming responses
)
```

### Using Cloud APIs

You can also use cloud-based LLM providers:

```python
# OpenAI GPT-4
model_config = ModelConfig(
    base_url="https://api.openai.com/v1",
    api_key="your-openai-api-key",
    model_name="gpt-4-turbo-preview",
)

# Anthropic Claude (via OpenAI-compatible proxy)
model_config = ModelConfig(
    base_url="https://your-proxy.com/v1",
    api_key="your-api-key",
    model_name="claude-3-opus-20240229",
)
```

---

## 🔨 Creating Custom Tools

Extend the agent with your own custom tools:

```python
from typing import Any
from coding_agent.tools import Tool, ToolResult


class WeatherTool(Tool):
    """Custom tool to fetch weather data."""
    
    @property
    def name(self) -> str:
        return "get_weather"
    
    @property
    def description(self) -> str:
        return "Get current weather for a specified city"
    
    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string", 
                    "description": "Name of the city"
                },
                "unit": {
                    "type": "string", 
                    "description": "Temperature unit (celsius or fahrenheit)",
                    "enum": ["celsius", "fahrenheit"]
                }
            },
            "required": ["city"],
        }
    
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the weather lookup."""
        city = kwargs.get("city")
        unit = kwargs.get("unit", "celsius")
        
        # Your implementation here
        try:
            # Simulated weather data
            weather_data = f"Weather in {city}: 22°{unit[0].upper()}"
            return ToolResult(success=True, output=weather_data)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Register and use the custom tool
with CodingAgent() as agent:
    agent.register_tool(WeatherTool())
    response = agent.run("What's the weather in London?")
    print(response)
```

### Tool Best Practices

1. **Single Responsibility**: Each tool should do one thing well
2. **Clear Descriptions**: Write detailed descriptions for the LLM
3. **Proper Schemas**: Define clear JSON schemas for parameters
4. **Error Handling**: Always handle exceptions gracefully
5. **Security**: Validate inputs and respect workspace boundaries

### Tool Development Workflow

1. **Identify the Need**: Determine what capability is missing
2. **Design the Interface**: Define clear inputs and outputs
3. **Implement the Tool**: Extend the `Tool` base class
4. **Write Tests**: Ensure reliable behavior
5. **Register and Test**: Add to agent and test with real scenarios

```python
# Example: Testing a custom tool
import pytest
from coding_agent.tools import ToolResult
from your_module import YourCustomTool

def test_your_tool():
    tool = YourCustomTool()
    result = tool.execute(param1="value1")
    
    assert isinstance(result, ToolResult)
    assert result.success is True
    assert "expected" in result.output
```

---

## 🧪 Testing Your Tools

The project includes comprehensive tests for all built-in tools. When creating custom tools, follow similar testing patterns:

```python
# tests/test_custom_tools.py
import pytest
from coding_agent.tools import ToolResult
from coding_agent.tools.browser import BrowserNavigateTool

class TestBrowserTools:
    def test_navigate_valid_url(self):
        tool = BrowserNavigateTool()
        result = tool.execute(url="https://example.com")
        assert result.success is True
        assert "navigated" in result.output.lower()
    
    def test_navigate_invalid_url(self):
        tool = BrowserNavigateTool()
        result = tool.execute(url="not-a-valid-url")
        assert result.success is False
        assert "error" in result.output.lower()
```

Run tests with pytest:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_custom_tools.py

# Run with coverage
pytest --cov=coding_agent tests/
```

---

## 🎨 Design Principles

### KISS (Keep It Simple, Stupid)

- Each tool has a single, clear responsibility
- Minimal abstraction layers
- Straightforward control flow
- Easy to understand and debug

### DRY (Don't Repeat Yourself)

- Shared utilities in common modules
- Centralized tool registry
- Reusable message and configuration classes
- Consistent patterns across components

### Google Style Guide

- Comprehensive docstrings with Args, Returns, Raises
- Type hints throughout the codebase
- Clear naming conventions
- Well-organized module structure

### Security First

- Workspace isolation for file operations
- Input validation on all tool parameters
- Timeout limits on tool execution
- Safe shell command execution

---

## 📦 Requirements

### Core Dependencies

- **Python**: 3.10 or higher
- **httpx**: Async HTTP client for LLM API calls

### Optional Dependencies

- **Ollama**: For local LLM inference
- **pytest**: For running tests
- **black**: For code formatting
- **mypy**: For type checking

### Recommended Models

| Model | Size | Performance | Use Case |
|-------|------|-------------|----------|
| Qwen2.5-Coder-7B | 7B | Excellent | General coding tasks |
| CodeLlama-7B | 7B | Very Good | Code completion |
| DeepSeek-Coder-6.7B | 6.7B | Excellent | Multi-language support |
| StarCoder2-7B | 7B | Very Good | Open-source alternative |

---

## 🧪 Testing

Run the included examples to verify your setup:

```bash
# Test basic functionality
python -m coding_agent.examples.basic_usage

# Test custom tools
python -m coding_agent.examples.custom_tools
```

---

## 📄 License

This project is licensed under the **MIT License** - see the LICENSE file for details.

```
MIT License

Copyright (c) 2024 Coding Agent Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📞 Support

For issues, questions, or suggestions:

- 📖 Check the documentation in `/workspace/coding_agent/README.md`
- 🐛 Report bugs via issue tracker
- 💬 Discuss features and improvements

---

<div align="center">

**Happy Coding! 🚀**

Built with ❤️ using local LLMs

</div>
