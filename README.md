# Coding Agent Project

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**A modular and scalable coding agent architecture designed for on-device execution with local LLM models**

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Available Tools](#available-tools)
- [Configuration](#configuration)
- [Creating Custom Tools](#creating-custom-tools)
- [Design Principles](#design-principles)
- [Requirements](#requirements)
- [License](#license)

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

### Step 1: Install Dependencies

```bash
cd /workspace
pip install httpx
```

For development with additional tools:

```bash
pip install -r coding_agent/requirements.txt
```

### Step 2: Setup Local LLM (Recommended)

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

---

## 🛠️ Available Tools

The coding agent comes with a comprehensive set of built-in tools:

| Tool | Class | Description |
|------|-------|-------------|
| **read_file** | `ReadFileTool` | Read contents of a file |
| **write_file** | `WriteFileTool` | Write content to a file (creates or overwrites) |
| **list_dir** | `ListDirTool` | List directory contents with file details |
| **search_files** | `SearchFilesTool` | Search files by glob pattern |
| **run_command** | `RunCommandTool` | Execute shell commands safely |
| **run_python** | `RunPythonTool` | Execute Python code snippets |

### Tool Security

All file system tools operate within a configured `workspace_root` directory to prevent unauthorized access to sensitive files outside the project scope.

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
