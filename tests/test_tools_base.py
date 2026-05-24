"""Tests for the base tool classes and registry."""

import pytest

from coding_agent.tools.base import Tool, ToolResult, ToolRegistry


class TestToolResult:
    """Tests for the ToolResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful tool result."""
        result = ToolResult(success=True, output="Success output")
        assert result.success is True
        assert result.output == "Success output"
        assert result.error is None

    def test_failed_result_with_error(self):
        """Test creating a failed tool result with error message."""
        result = ToolResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.output == ""
        assert result.error == "Something went wrong"

    def test_failed_result_with_output_and_error(self):
        """Test creating a failed result with both output and error."""
        result = ToolResult(success=False, output="Partial output", error="Error occurred")
        assert result.success is False
        assert result.output == "Partial output"
        assert result.error == "Error occurred"

    def test_str_representation_success(self):
        """Test string representation for successful result."""
        result = ToolResult(success=True, output="Output text")
        assert str(result) == "Output text"

    def test_str_representation_failure(self):
        """Test string representation for failed result."""
        result = ToolResult(success=False, error="Test error")
        assert str(result) == "Error: Test error"


class MockTool(Tool):
    """Mock tool for testing purposes."""

    def __init__(self, name: str = "mock_tool", description: str = "A mock tool"):
        self._name = name
        self._description = description
        self._schema = {
            "type": "object",
            "properties": {"param1": {"type": "string"}},
            "required": ["param1"],
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def schema(self) -> dict:
        return self._schema

    def execute(self, **kwargs) -> ToolResult:
        param1 = kwargs.get("param1", "")
        return ToolResult(success=True, output=f"Executed with param1={param1}")


class TestToolRegistry:
    """Tests for the ToolRegistry class."""

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        assert "mock_tool" in registry.list_tools()

    def test_register_duplicate_tool_raises_error(self):
        """Test that registering a duplicate tool raises ValueError."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool)

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        registry.unregister("mock_tool")
        assert "mock_tool" not in registry.list_tools()

    def test_unregister_nonexistent_tool_raises_error(self):
        """Test that unregistering a non-existent tool raises KeyError."""
        registry = ToolRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.unregister("nonexistent")

    def test_get_tool(self):
        """Test getting a tool by name."""
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)
        retrieved = registry.get("test_tool")
        assert retrieved is tool

    def test_get_nonexistent_tool_raises_error(self):
        """Test that getting a non-existent tool raises KeyError."""
        registry = ToolRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    def test_list_tools(self):
        """Test listing all registered tools."""
        registry = ToolRegistry()
        registry.register(MockTool(name="tool1"))
        registry.register(MockTool(name="tool2"))
        tools = registry.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_get_all_schemas(self):
        """Test getting all tool schemas."""
        registry = ToolRegistry()
        tool = MockTool(name="schema_test")
        registry.register(tool)
        schemas = registry.get_all_schemas()
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "schema_test"

    def test_execute_tool(self):
        """Test executing a tool through the registry."""
        registry = ToolRegistry()
        tool = MockTool(name="exec_test")
        registry.register(tool)
        result = registry.execute("exec_test", param1="test_value")
        assert result.success is True
        assert "test_value" in result.output

    def test_execute_nonexistent_tool_raises_error(self):
        """Test that executing a non-existent tool raises KeyError."""
        registry = ToolRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.execute("nonexistent", param1="test")


class TestMockTool:
    """Tests for the MockTool implementation."""

    def test_tool_properties(self):
        """Test tool property accessors."""
        tool = MockTool(name="my_tool", description="My description")
        assert tool.name == "my_tool"
        assert tool.description == "My description"
        assert isinstance(tool.schema, dict)

    def test_tool_execute(self):
        """Test tool execution."""
        tool = MockTool()
        result = tool.execute(param1="hello")
        assert result.success is True
        assert "hello" in result.output

    def test_tool_to_dict(self):
        """Test converting tool to dictionary."""
        tool = MockTool(name="dict_test", description="Dict test tool")
        tool_dict = tool.to_dict()
        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "dict_test"
        assert tool_dict["function"]["description"] == "Dict test tool"
        assert "parameters" in tool_dict["function"]
