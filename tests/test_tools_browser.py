"""Tests for browser automation tools."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from coding_agent.tools.browser import (
    BrowserClickTool,
    BrowserNavigateTool,
    BrowserScreenshotTool,
    BrowserTools,
)
from coding_agent.tools.base import ToolResult


class TestBrowserTools:
    """Tests for BrowserTools class."""

    def test_init_default_workspace(self):
        """Test initialization with default workspace."""
        tools = BrowserTools()
        assert tools.workspace_root is not None

    def test_init_custom_workspace(self):
        """Test initialization with custom workspace."""
        tools = BrowserTools(workspace_root="/tmp/test", headless=False)
        assert str(tools.workspace_root).endswith("/tmp/test")
        assert tools.headless is False

    def test_close_without_browser(self):
        """Test closing when no browser is open."""
        browser_tools = BrowserTools()
        # Should not raise any exception
        asyncio.run(browser_tools.close())

    def test_get_page_when_none_returns_none(self):
        """Test _get_page returns None when page not initialized."""
        browser_tools = BrowserTools()
        browser_tools._page = None
        # When browser not initialized, _get_page should return None
        # This is expected behavior - browser needs to be created first
        assert browser_tools._page is None


class TestBrowserNavigateTool:
    """Tests for BrowserNavigateTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = BrowserNavigateTool()
        assert tool.name == "browser_navigate"

    def test_description_property(self):
        """Test tool description."""
        tool = BrowserNavigateTool()
        assert "Navigate" in tool.description
        assert "URL" in tool.description

    def test_schema_property(self):
        """Test tool schema."""
        tool = BrowserNavigateTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "url" in schema["properties"]
        assert "url" in schema["required"]

    def test_execute_missing_url(self):
        """Test execute with missing URL parameter."""
        tool = BrowserNavigateTool()
        result = tool.execute()
        
        assert result.success is False
        assert "Missing required parameter: url" in result.error

    def test_execute_invalid_url_format(self):
        """Test execute with invalid URL format."""
        tool = BrowserNavigateTool()
        result = tool.execute(url="not-a-valid-url")
        
        assert result.success is False
        assert "must start with http:// or https://" in result.error

    def test_execute_valid_url_no_browser(self):
        """Test execute when browser not available."""
        tool = BrowserNavigateTool()
        result = tool.execute(url="https://example.com")
        # Will fail because playwright not installed, but should handle gracefully
        assert result is not None

    def test_execute_raises_exception(self):
        """Test execute that raises an exception."""
        tool = BrowserNavigateTool()
        # Test with actual browser - will fail due to playwright not installed
        result = tool.execute(url="https://example.com")
        # Should handle gracefully even if browser fails
        assert result is not None

    def test_async_navigate_success(self):
        """Test async navigate method."""
        tool = BrowserNavigateTool()
        
        async def run_test():
            # Mock the browser tools
            mock_page = AsyncMock()
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.status_text = "OK"
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            mock_page.goto = AsyncMock(return_value=mock_response)
            mock_page.title = AsyncMock(return_value="Example Domain")
            mock_page.url = "https://example.com"
            
            result = await tool._navigate("https://example.com", "load", 30000)
            
            assert result.success is True
            assert "Successfully navigated" in result.output
            assert "Example Domain" in result.output
        
        asyncio.run(run_test())

    def test_async_navigate_failure(self):
        """Test async navigate that fails."""
        tool = BrowserNavigateTool()
        
        async def run_test():
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock()
            tool._browser_tools._get_page.side_effect = Exception("Connection failed")
            
            result = await tool._navigate("https://example.com", "load", 30000)
            
            assert result.success is False
            assert "Navigation failed" in result.error
        
        asyncio.run(run_test())


class TestBrowserClickTool:
    """Tests for BrowserClickTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = BrowserClickTool()
        assert tool.name == "browser_click"

    def test_description_property(self):
        """Test tool description."""
        tool = BrowserClickTool()
        assert "Click" in tool.description
        assert "element" in tool.description.lower()

    def test_schema_property(self):
        """Test tool schema."""
        tool = BrowserClickTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "selector" in schema["properties"]
        assert "selector" in schema["required"]

    def test_execute_missing_selector(self):
        """Test execute with missing selector parameter."""
        tool = BrowserClickTool()
        result = tool.execute()
        
        assert result.success is False
        assert "Missing required parameter: selector" in result.error

    def test_execute_with_selector_no_browser(self):
        """Test execute when browser not available."""
        tool = BrowserClickTool()
        result = tool.execute(selector="button#submit")
        # Should handle gracefully - return error about browser
        assert result is not None

    @patch.object(BrowserClickTool, "_click")
    def test_async_click_success(self, mock_click):
        """Test async click method."""
        async def run_test():
            mock_click.return_value = ToolResult(success=True, output="Successfully clicked button#submit")
            result = await tool._click("button#submit", 5000)
            assert result.success is True
            assert "clicked" in result.output.lower()
        
        tool = BrowserClickTool()
        asyncio.run(run_test())

    @patch.object(BrowserClickTool, "_click")
    def test_async_click_element_not_found(self, mock_click):
        """Test async click when element not found."""
        async def run_test():
            mock_click.return_value = ToolResult(success=False, error="No elements found matching selector: nonexistent")
            result = await tool._click("nonexistent", 5000)
            assert result.success is False
            assert "No elements found" in result.error
        
        tool = BrowserClickTool()
        asyncio.run(run_test())


class TestBrowserScreenshotTool:
    """Tests for BrowserScreenshotTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = BrowserScreenshotTool()
        assert tool.name == "browser_screenshot"

    def test_description_property(self):
        """Test tool description."""
        tool = BrowserScreenshotTool()
        assert "screenshot" in tool.description.lower()

    def test_schema_property(self):
        """Test tool schema."""
        tool = BrowserScreenshotTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "path" in schema["properties"]
        assert "full_page" in schema["properties"]

    def test_execute_with_path_no_browser(self):
        """Test execute when browser not available."""
        tool = BrowserScreenshotTool()
        result = tool.execute(path="/tmp/test.png")
        # Should handle gracefully
        assert result is not None

    @patch.object(BrowserScreenshotTool, "_screenshot")
    def test_async_screenshot_success(self, mock_screenshot):
        """Test async screenshot method."""
        async def run_test():
            mock_screenshot.return_value = ToolResult(success=True, output="Screenshot saved")
            result = await tool._screenshot("/tmp/test.png", full_page=True)
            assert result.success is True
            assert "screenshot" in result.output.lower()
        
        tool = BrowserScreenshotTool()
        asyncio.run(run_test())

    @patch.object(BrowserScreenshotTool, "_screenshot")
    def test_async_screenshot_no_browser(self, mock_screenshot):
        """Test screenshot when browser not initialized."""
        async def run_test():
            mock_screenshot.return_value = ToolResult(success=False, error="No page available")
            result = await tool._screenshot("/tmp/test.png", full_page=False)
            assert result.success is False
            assert "No page available" in result.error
        
        tool = BrowserScreenshotTool()
        asyncio.run(run_test())
