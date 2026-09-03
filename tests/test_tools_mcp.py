"""Tests for MCP (Model Context Protocol) integration tools."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from coding_agent.tools.mcp_tools import (
    MCPClientManager,
    MCPToolWrapper,
    connect_mcp,
)
from coding_agent.tools.base import ToolRegistry, ToolResult


class MockMCPTool:
    """Mock MCP tool for testing purposes."""

    def __init__(self, name: str, description: str = None, input_schema: dict = None):
        self.name = name
        self.description = description or f"Test tool {name}"
        self.inputSchema = input_schema or {
            "type": "object",
            "properties": {"param": {"type": "string"}},
            "required": ["param"],
        }


class MockCallToolResult:
    """Mock CallToolResult for testing purposes."""
    
    def __init__(self, text: str, is_error: bool = False):
        content_item = MagicMock()
        content_item.text = text
        self.content = [content_item]
        self.data = None
        self.is_error = is_error


class MockMCPClient:
    """Mock MCP client for testing purposes."""

    def __init__(self):
        self.tools = []
        self.is_connected = False

    async def __aenter__(self):
        self.is_connected = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.is_connected = False

    async def list_tools(self):
        """Return list of mock tools."""
        return self.tools

    async def call_tool(self, tool_name: str, kwargs: dict):
        """Mock tool call result."""
        return MockCallToolResult(
            text=f"Result from {tool_name} with params: {kwargs}",
            is_error=False
        )


class TestMCPToolWrapper:
    """Tests for the MCPToolWrapper class."""

    def test_wrapper_initialization(self):
        """Test initializing the wrapper with an MCP tool."""
        mcp_tool = MockMCPTool(name="test_tool", description="Test description")
        mcp_client = MockMCPClient()
        
        wrapper = MCPToolWrapper(mcp_tool, mcp_client)
        
        assert wrapper.name == "test_tool"
        assert wrapper.description == "Test description"
        assert wrapper.schema == mcp_tool.inputSchema

    def test_wrapper_default_description(self):
        """Test wrapper uses default description when none provided."""
        mcp_tool = MockMCPTool(name="simple_tool", description=None)
        mcp_client = MockMCPClient()
        
        wrapper = MCPToolWrapper(mcp_tool, mcp_client)
        
        assert "simple_tool" in wrapper.description

    def test_wrapper_execute_success(self):
        """Test successful tool execution."""
        mcp_tool = MockMCPTool(name="exec_test")
        mcp_client = MockMCPClient()
        mcp_client.tools = [mcp_tool]
        
        wrapper = MCPToolWrapper(mcp_tool, mcp_client)
        
        with patch.object(wrapper, '_async_call_tool', new_callable=AsyncMock) as mock_call:
            mock_result = MockCallToolResult(text="Success output", is_error=False)
            mock_call.return_value = mock_result
            
            result = wrapper.execute(param="test_value")
            
            assert result.success is True
            assert "Success output" in result.output
            assert result.error is None

    def test_wrapper_execute_with_error(self):
        """Test tool execution that returns an error."""
        mcp_tool = MockMCPTool(name="error_test")
        mcp_client = MockMCPClient()
        
        wrapper = MCPToolWrapper(mcp_tool, mcp_client)
        
        with patch.object(wrapper, '_async_call_tool', new_callable=AsyncMock) as mock_call:
            mock_result = MockCallToolResult(text="Error occurred", is_error=True)
            mock_call.return_value = mock_result
            
            result = wrapper.execute(param="bad_value")
            
            assert result.success is False
            assert result.error == "MCP tool returned an error"

    def test_wrapper_execute_exception(self):
        """Test tool execution that raises an exception."""
        mcp_tool = MockMCPTool(name="exception_test")
        mcp_client = MockMCPClient()
        
        wrapper = MCPToolWrapper(mcp_tool, mcp_client)
        
        with patch.object(wrapper, '_async_call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("Unexpected error")
            
            result = wrapper.execute(param="test")
            
            assert result.success is False
            assert "MCP tool execution error" in result.error

    def test_wrapper_parse_result_with_data_attribute(self):
        """Test parsing result that has data attribute instead of content."""
        mcp_tool = MockMCPTool(name="data_test")
        mcp_client = MockMCPClient()
        
        wrapper = MCPToolWrapper(mcp_tool, mcp_client)
        
        mock_result = MagicMock()
        mock_result.content = None
        mock_result.data = {"key": "value"}
        mock_result.is_error = False
        
        parsed = wrapper._parse_result(mock_result)
        
        assert parsed.success is True
        assert "{'key': 'value'}" in parsed.output

    def test_wrapper_async_execute(self):
        """Test async tool execution."""
        mcp_tool = MockMCPTool(name="async_test")
        mcp_client = MockMCPClient()
        
        wrapper = MCPToolWrapper(mcp_tool, mcp_client)
        
        async def run_test():
            with patch.object(wrapper, '_mcp_client') as mock_client:
                mock_result = MockCallToolResult(text="Async result", is_error=False)
                mock_client.call_tool = AsyncMock(return_value=mock_result)
                
                result = await wrapper.async_execute(param="async_test")
                
                assert result.success is True
                assert "Async result" in result.output
        
        asyncio.run(run_test())


class TestMCPClientManager:
    """Tests for the MCPClientManager class."""

    def test_manager_initialization(self):
        """Test initializing the manager."""
        manager = MCPClientManager()
        
        assert isinstance(manager.registry, ToolRegistry)
        assert len(manager._clients) == 0
        assert len(manager._wrapped_tools) == 0

    def test_manager_initialization_with_registry(self):
        """Test initializing the manager with custom registry."""
        custom_registry = ToolRegistry()
        manager = MCPClientManager(registry=custom_registry)
        
        assert manager.registry is custom_registry

    @pytest.mark.asyncio
    async def test_connect_to_server(self):
        """Test connecting to an MCP server."""
        manager = MCPClientManager()
        mock_transport = MagicMock()
        mock_transport.name = "test_server"
        
        mock_client = MockMCPClient()
        mock_tool = MockMCPTool(name="discovered_tool")
        mock_client.tools = [mock_tool]
        
        with patch('fastmcp.client.Client', return_value=mock_client):
            tools = await manager.connect(mock_transport, server_name="test_server")
            
            assert len(tools) == 1
            assert tools[0].name == "discovered_tool"
            assert "test_server" in manager._clients

    @pytest.mark.asyncio
    async def test_connect_with_prefix(self):
        """Test connecting with tool name prefix."""
        manager = MCPClientManager()
        mock_transport = MagicMock()
        
        mock_client = MockMCPClient()
        mock_tool = MockMCPTool(name="base_tool")
        mock_client.tools = [mock_tool]
        
        with patch('fastmcp.client.Client', return_value=mock_client):
            tools = await manager.connect(
                mock_transport,
                server_name="prefixed_server",
                prefix="myprefix"
            )
            
            assert len(tools) == 1
            # The wrapper keeps the original tool name
            assert tools[0].name == "base_tool"
            # But it's registered in the registry with the prefix
            assert "myprefix_base_tool" in manager.get_registered_tools()

    @pytest.mark.asyncio
    async def test_connect_without_server_name(self):
        """Test connecting without providing server name."""
        manager = MCPClientManager()
        mock_transport = MagicMock()
        mock_transport.name = "named_transport"
        
        mock_client = MockMCPClient()
        mock_client.tools = []
        
        with patch('fastmcp.client.Client', return_value=mock_client):
            tools = await manager.connect(mock_transport)
            
            # Should use transport.name as server_name
            assert "named_transport" in manager._clients

    @pytest.mark.asyncio
    async def test_disconnect_from_server(self):
        """Test disconnecting from an MCP server."""
        manager = MCPClientManager()
        mock_transport = MagicMock()
        
        mock_client = MockMCPClient()
        mock_tool = MockMCPTool(name="temp_tool")
        mock_client.tools = [mock_tool]
        
        with patch('fastmcp.client.Client', return_value=mock_client):
            await manager.connect(mock_transport, server_name="temp_server")
            assert len(manager._clients) == 1
            
            await manager.disconnect("temp_server")
            
            assert len(manager._clients) == 0
            assert len(manager._wrapped_tools) == 0

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_server(self):
        """Test disconnecting from a server that doesn't exist."""
        manager = MCPClientManager()
        
        # Should not raise an error
        await manager.disconnect("nonexistent_server")

    @pytest.mark.asyncio
    async def test_disconnect_all(self):
        """Test disconnecting from all servers."""
        manager = MCPClientManager()
        
        mock_transport1 = MagicMock()
        mock_transport1.name = "server1"
        mock_transport2 = MagicMock()
        mock_transport2.name = "server2"
        
        mock_client1 = MockMCPClient()
        mock_client1.tools = []
        mock_client2 = MockMCPClient()
        mock_client2.tools = []
        
        with patch('fastmcp.client.Client') as mock_client_class:
            mock_client_class.side_effect = [mock_client1, mock_client2]
            
            await manager.connect(mock_transport1)
            await manager.connect(mock_transport2)
            
            assert len(manager._clients) == 2
            
            await manager.disconnect_all()
            
            assert len(manager._clients) == 0

    @pytest.mark.asyncio
    async def test_get_registered_tools(self):
        """Test getting list of registered tool names."""
        manager = MCPClientManager()
        mock_transport = MagicMock()
        
        mock_client = MockMCPClient()
        mock_tool1 = MockMCPTool(name="tool_a")
        mock_tool2 = MockMCPTool(name="tool_b")
        mock_client.tools = [mock_tool1, mock_tool2]
        
        with patch('fastmcp.client.Client', return_value=mock_client):
            await manager.connect(mock_transport, server_name="tools_server")
            
            registered = manager.get_registered_tools()
            
            assert len(registered) == 2
            assert "tool_a" in registered
            assert "tool_b" in registered

    def test_fastmcp_not_installed(self):
        """Test behavior when fastmcp is not installed."""
        manager = MCPClientManager()
        mock_transport = MagicMock()
        
        with patch.dict('sys.modules', {'fastmcp.client': None}):
            with pytest.raises(ImportError, match="fastmcp is required"):
                asyncio.run(manager.connect(mock_transport))


class TestConnectMCPFunction:
    """Tests for the connect_mcp convenience function."""

    @pytest.mark.asyncio
    async def test_connect_mcp_creates_manager(self):
        """Test that connect_mcp creates and returns a manager."""
        mock_transport = MagicMock()
        mock_transport.name = "test_server"
        
        mock_client = MockMCPClient()
        mock_client.tools = []
        
        with patch('fastmcp.client.Client', return_value=mock_client):
            manager = await connect_mcp(mock_transport)
            
            assert isinstance(manager, MCPClientManager)
            assert "test_server" in manager._clients

    @pytest.mark.asyncio
    async def test_connect_mcp_with_custom_registry(self):
        """Test connect_mcp with custom registry."""
        custom_registry = ToolRegistry()
        mock_transport = MagicMock()
        mock_transport.name = "custom_server"
        
        mock_client = MockMCPClient()
        mock_client.tools = []
        
        with patch('fastmcp.client.Client', return_value=mock_client):
            manager = await connect_mcp(mock_transport, registry=custom_registry)
            
            assert manager.registry is custom_registry

    @pytest.mark.asyncio
    async def test_connect_mcp_with_prefix(self):
        """Test connect_mcp with tool name prefix."""
        mock_transport = MagicMock()
        mock_transport.name = "prefix_server"
        
        mock_client = MockMCPClient()
        mock_tool = MockMCPTool(name="original_tool")
        mock_client.tools = [mock_tool]
        
        with patch('fastmcp.client.Client', return_value=mock_client):
            manager = await connect_mcp(mock_transport, prefix="pre")
            
            registered = manager.get_registered_tools()
            assert len(registered) == 1
            assert "pre_original_tool" in registered
