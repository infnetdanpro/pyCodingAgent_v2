# Coding Agent

A modular and scalable coding agent architecture designed for on-device execution with local LLM models.

## Features

- **OpenAI-Compatible API**: Works with local models like Qwen2.5-Coder via Ollama or any OpenAI-compatible endpoint
- **Modular Tool System**: Easy to extend with custom tools
- **ReAct Pattern**: Reasoning + Acting loop for complex task completion
- **Conversation History**: Persistent context across sessions
- **Google Style Guide**: Clean, well-documented code following best practices
- **KISS & DRY**: Simple, maintainable architecture

## Architecture

```
coding_agent/
├── config/          # Configuration classes (Settings, ModelConfig)
├── core/            # Core agent logic (CodingAgent, ConversationContext)
├── llm/             # LLM client (OpenAI-compatible)
├── tools/           # Tool definitions and implementations
├── utils/           # Utility functions
└── examples/        # Usage examples
```

## Installation

```bash
# Install dependencies
pip install httpx

# For development
pip install -r requirements-dev.txt
```

## Quick Start

### 1. Setup Local LLM

Install [Ollama](https://ollama.ai/) and pull a coding model:

```bash
ollama pull qwen2.5-coder:7b
```

### 2. Basic Usage

```python
from coding_agent.config import ModelConfig, Settings
from coding_agent.core import CodingAgent
from coding_agent.tools import ReadFileTool, WriteFileTool, ListDirTool
from coding_agent.utils import setup_logging

setup_logging(level="INFO")

settings = Settings(workspace_dir=".")
model_config = ModelConfig(
    base_url="http://localhost:11434/v1",
    model_name="qwen2.5-coder:7b",
)

with CodingAgent(settings=settings, model_config=model_config) as agent:
    # Register tools
    agent.register_tool(ReadFileTool())
    agent.register_tool(WriteFileTool())
    agent.register_tool(ListDirTool())

    # Run agent
    response = agent.run("List all Python files in the current directory")
    print(response)
```

### 3. Run Example

```bash
python -m coding_agent.examples.basic_usage
```

## Creating Custom Tools

```python
from typing import Any
from coding_agent.tools import Tool, ToolResult

class MyCustomTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Description of what this tool does"

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parameter description"},
            },
            "required": ["param1"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        param1 = kwargs.get("param1")
        # Your implementation here
        return ToolResult(success=True, output="Result")
```

## Available Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read contents of a file |
| `write_file` | Write content to a file |
| `list_dir` | List directory contents |
| `search_files` | Search files by glob pattern |
| `run_command` | Execute shell commands |
| `run_python` | Execute Python code snippets |
| `git_diff` | Check git diff against main/master branch |
| `git_commit` | Create a git commit with specified message |
| `git_push` | Push git commits to remote repository |
| `git_pull_request` | Create pull requests on GitHub or GitLab |

## Configuration

### Settings

```python
Settings(
    workspace_dir=".",           # Root directory for operations
    max_iterations=50,           # Maximum agent loop iterations
    timeout_seconds=300,         # Tool execution timeout
    log_level="INFO",            # Logging level
    enable_history=True,         # Persist conversation history
    history_dir=".agent_history",# History storage directory
    max_context_length=128000,   # Max context tokens
    temperature=0.7,             # LLM temperature
    top_p=0.95,                  # LLM top_p
)
```

### ModelConfig

```python
ModelConfig(
    base_url="http://localhost:11434/v1",  # API endpoint
    api_key="ollama",                       # API key (dummy for local)
    model_name="qwen2.5-coder:7b",          # Model name
    max_tokens=4096,                        # Max response tokens
    timeout=120,                            # Request timeout
    retry_count=3,                          # Retry attempts
    stream=True,                            // Stream responses
)
```

## Design Principles

### KISS (Keep It Simple, Stupid)
- Each tool has a single, clear responsibility
- Minimal abstraction layers
- Straightforward control flow

### DRY (Don't Repeat Yourself)
- Shared utilities in common modules
- Centralized tool registry
- Reusable message and configuration classes

### Google Style Guide
- Comprehensive docstrings
- Type hints throughout
- Clear naming conventions

## License

MIT License
