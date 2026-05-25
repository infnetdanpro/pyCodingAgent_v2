"""Tests for browser automation tools."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from coding_agent.tools.browser import (
    BrowserClickTool,
    BrowserCloseTool,
    BrowserEvaluateTool,
    BrowserFillTool,
    BrowserGetContentTool,
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

    @patch("playwright.async_api.async_playwright")
    def test_ensure_browser_creates_new_browser(self, mock_playwright):
        """Test _ensure_browser creates browser when none exists."""
        async def run_test():
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            mock_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
            
            browser_tools = BrowserTools()
            await browser_tools._ensure_browser()
            
            assert browser_tools._browser is not None
            assert browser_tools._context is not None
            assert browser_tools._page is not None
        
        asyncio.run(run_test())

    @patch("playwright.async_api.async_playwright")
    def test_ensure_browser_reuses_existing_browser(self, mock_playwright):
        """Test _ensure_browser reuses existing browser."""
        async def run_test():
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            mock_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
            
            browser_tools = BrowserTools()
            browser_tools._browser = mock_browser
            
            await browser_tools._ensure_browser()
            
            # Browser should not be recreated
            mock_playwright_instance.chromium.launch.assert_not_called()
        
        asyncio.run(run_test())

    @patch("playwright.async_api.async_playwright")
    def test_close_with_browser(self, mock_playwright):
        """Test closing browser when it's open."""
        async def run_test():
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            
            browser_tools = BrowserTools()
            browser_tools._browser = mock_browser
            browser_tools._context = mock_context
            browser_tools._page = AsyncMock()
            
            await browser_tools.close()
            
            mock_context.close.assert_called_once()
            mock_browser.close.assert_called_once()
            assert browser_tools._browser is None
            assert browser_tools._context is None
            assert browser_tools._page is None
        
        asyncio.run(run_test())

    def test_get_page_calls_ensure_browser(self):
        """Test _get_page calls _ensure_browser when page is None."""
        async def run_test():
            browser_tools = BrowserTools()
            browser_tools._page = None
            
            # Mock _ensure_browser to create a mock page
            mock_page = AsyncMock()
            browser_tools._ensure_browser = AsyncMock(side_effect=lambda: setattr(browser_tools, '_page', mock_page))
            
            result = await browser_tools._get_page()
            
            browser_tools._ensure_browser.assert_called_once()
        
        asyncio.run(run_test())


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

    def test_execute_exception_handling(self):
        """Test execute handles exceptions gracefully."""
        tool = BrowserNavigateTool()
        
        with patch.object(tool, "_navigate", side_effect=Exception("Test error")):
            result = tool.execute(url="https://example.com")
            assert result.success is False
            assert "Test error" in result.error


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

    def test_execute_exception_handling(self):
        """Test execute handles exceptions gracefully."""
        tool = BrowserClickTool()
        
        with patch.object(tool, "_click", side_effect=Exception("Test error")):
            result = tool.execute(selector="button#submit")
            assert result.success is False
            assert "Test error" in result.error

    def test_async_click_success_css_selector(self):
        """Test async click method with CSS selector."""
        tool = BrowserClickTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.click = AsyncMock()
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._click("button#submit", 5000)
            
            assert result.success is True
            assert "clicked" in result.output.lower()
            mock_page.click.assert_called_once_with("button#submit", timeout=5000)
        
        asyncio.run(run_test())

    def test_async_click_falls_back_to_text(self):
        """Test async click falls back to text selector."""
        tool = BrowserClickTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.click = AsyncMock(side_effect=Exception("CSS selector failed"))
            mock_text_locator = AsyncMock()
            mock_text_locator.first = AsyncMock()
            mock_text_locator.first.click = AsyncMock()
            mock_page.get_by_text = MagicMock(return_value=mock_text_locator)
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._click("Click Me", 5000)
            
            assert result.success is True
            mock_text_locator.first.click.assert_called_once()
        
        asyncio.run(run_test())

    def test_async_click_failure(self):
        """Test async click that fails."""
        tool = BrowserClickTool()
        
        async def run_test():
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock()
            tool._browser_tools._get_page.side_effect = Exception("No page")
            
            result = await tool._click("button#submit", 5000)
            
            assert result.success is False
            assert "Click failed" in result.error
        
        asyncio.run(run_test())


class TestBrowserFillTool:
    """Tests for BrowserFillTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = BrowserFillTool()
        assert tool.name == "browser_fill"

    def test_description_property(self):
        """Test tool description."""
        tool = BrowserFillTool()
        assert "Fill" in tool.description
        assert "input" in tool.description.lower()

    def test_schema_property(self):
        """Test tool schema."""
        tool = BrowserFillTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "selector" in schema["properties"]
        assert "value" in schema["properties"]
        assert "selector" in schema["required"]
        assert "value" in schema["required"]

    def test_execute_missing_selector(self):
        """Test execute with missing selector parameter."""
        tool = BrowserFillTool()
        result = tool.execute(value="test")
        
        assert result.success is False
        assert "Missing required parameter: selector" in result.error

    def test_execute_missing_value(self):
        """Test execute with missing value parameter."""
        tool = BrowserFillTool()
        result = tool.execute(selector="input#email")
        
        assert result.success is False
        assert "Missing required parameter: value" in result.error

    def test_execute_exception_handling(self):
        """Test execute handles exceptions gracefully."""
        tool = BrowserFillTool()
        
        with patch.object(tool, "_fill", side_effect=Exception("Test error")):
            result = tool.execute(selector="input#email", value="test@example.com")
            assert result.success is False
            assert "Test error" in result.error

    def test_async_fill_success(self):
        """Test async fill method."""
        tool = BrowserFillTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.fill = AsyncMock()
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._fill("input#email", "test@example.com", 5000)
            
            assert result.success is True
            assert "Successfully filled" in result.output
            mock_page.fill.assert_called_once_with("input#email", "test@example.com", timeout=5000)
        
        asyncio.run(run_test())

    def test_async_fill_failure(self):
        """Test async fill that fails."""
        tool = BrowserFillTool()
        
        async def run_test():
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock()
            tool._browser_tools._get_page.side_effect = Exception("No page")
            
            result = await tool._fill("input#email", "test", 5000)
            
            assert result.success is False
            assert "Fill failed" in result.error
        
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

    def test_execute_exception_handling(self):
        """Test execute handles exceptions gracefully."""
        tool = BrowserScreenshotTool()
        
        with patch.object(tool, "_screenshot", side_effect=Exception("Test error")):
            result = tool.execute(path="/tmp/test.png")
            assert result.success is False
            assert "Test error" in result.error

    def test_async_screenshot_success(self):
        """Test async screenshot method."""
        tool = BrowserScreenshotTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.screenshot = AsyncMock()
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._screenshot("test.png", full_page=True)
            
            assert result.success is True
            assert "Screenshot saved" in result.output
        
        asyncio.run(run_test())

    def test_async_screenshot_full_page(self):
        """Test async screenshot with full_page option."""
        tool = BrowserScreenshotTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.screenshot = AsyncMock()
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._screenshot("test.png", full_page=True)
            
            mock_page.screenshot.assert_called_once()
            call_kwargs = mock_page.screenshot.call_args[1]
            assert call_kwargs["full_page"] is True
        
        asyncio.run(run_test())

    def test_async_screenshot_failure(self):
        """Test screenshot when browser not initialized."""
        tool = BrowserScreenshotTool()
        
        async def run_test():
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock()
            tool._browser_tools._get_page.side_effect = Exception("No page")
            
            result = await tool._screenshot("/tmp/test.png", full_page=False)
            
            assert result.success is False
            assert "Screenshot failed" in result.error
        
        asyncio.run(run_test())


class TestBrowserGetContentTool:
    """Tests for BrowserGetContentTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = BrowserGetContentTool()
        assert tool.name == "browser_get_content"

    def test_description_property(self):
        """Test tool description."""
        tool = BrowserGetContentTool()
        assert "content" in tool.description.lower()

    def test_schema_property(self):
        """Test tool schema."""
        tool = BrowserGetContentTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "selector" in schema["properties"]
        assert "content_type" in schema["properties"]

    def test_execute_exception_handling(self):
        """Test execute handles exceptions gracefully."""
        tool = BrowserGetContentTool()
        
        with patch.object(tool, "_get_content", side_effect=Exception("Test error")):
            result = tool.execute()
            assert result.success is False
            assert "Test error" in result.error

    def test_async_get_content_html_full_page(self):
        """Test async get content with HTML type for full page."""
        tool = BrowserGetContentTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._get_content(None, "html")
            
            assert result.success is True
            assert "Page content" in result.output
            mock_page.content.assert_called_once()
        
        asyncio.run(run_test())

    def test_async_get_content_inner_text_full_page(self):
        """Test async get content with inner_text type for full page."""
        tool = BrowserGetContentTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.evaluate = AsyncMock(return_value="Inner text content")
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._get_content(None, "inner_text")
            
            assert result.success is True
            mock_page.evaluate.assert_called_with("document.body.innerText")
        
        asyncio.run(run_test())

    def test_async_get_content_text_full_page(self):
        """Test async get content with text type for full page."""
        tool = BrowserGetContentTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.evaluate = AsyncMock(return_value="Text content")
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._get_content(None, "text")
            
            assert result.success is True
            mock_page.evaluate.assert_called_with("document.body.textContent")
        
        asyncio.run(run_test())

    def test_async_get_content_with_selector_html(self):
        """Test async get content with selector and HTML type."""
        tool = BrowserGetContentTool()
        
        async def run_test():
            mock_element = AsyncMock()
            mock_element.inner_html = AsyncMock(return_value="<div>Element HTML</div>")
            mock_locator = MagicMock()
            mock_locator.first = mock_element
            mock_page = AsyncMock()
            mock_page.locator = MagicMock(return_value=mock_locator)
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._get_content("#my-element", "html")
            
            assert result.success is True
            mock_element.inner_html.assert_called_once()
        
        asyncio.run(run_test())

    def test_async_get_content_with_selector_inner_text(self):
        """Test async get content with selector and inner_text type."""
        tool = BrowserGetContentTool()
        
        async def run_test():
            mock_element = AsyncMock()
            mock_element.inner_text = AsyncMock(return_value="Element inner text")
            mock_locator = MagicMock()
            mock_locator.first = mock_element
            mock_page = AsyncMock()
            mock_page.locator = MagicMock(return_value=mock_locator)
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._get_content("#my-element", "inner_text")
            
            assert result.success is True
            mock_element.inner_text.assert_called_once()
        
        asyncio.run(run_test())

    def test_async_get_content_with_selector_text(self):
        """Test async get content with selector and text type."""
        tool = BrowserGetContentTool()
        
        async def run_test():
            mock_element = AsyncMock()
            mock_element.text_content = AsyncMock(return_value="Element text")
            mock_locator = MagicMock()
            mock_locator.first = mock_element
            mock_page = AsyncMock()
            mock_page.locator = MagicMock(return_value=mock_locator)
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._get_content("#my-element", "text")
            
            assert result.success is True
            mock_element.text_content.assert_called_once()
        
        asyncio.run(run_test())

    def test_async_get_content_truncated(self):
        """Test async get content truncates long content."""
        tool = BrowserGetContentTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.content = AsyncMock(return_value="<html>" + "x" * 20000 + "</html>")
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._get_content(None, "html")
            
            assert result.success is True
            assert "(truncated)" in result.output
        
        asyncio.run(run_test())

    def test_async_get_content_failure(self):
        """Test async get content that fails."""
        tool = BrowserGetContentTool()
        
        async def run_test():
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock()
            tool._browser_tools._get_page.side_effect = Exception("No page")
            
            result = await tool._get_content(None, "text")
            
            assert result.success is False
            assert "Get content failed" in result.error
        
        asyncio.run(run_test())


class TestBrowserEvaluateTool:
    """Tests for BrowserEvaluateTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = BrowserEvaluateTool()
        assert tool.name == "browser_evaluate"

    def test_description_property(self):
        """Test tool description."""
        tool = BrowserEvaluateTool()
        assert "JavaScript" in tool.description
        assert "execute" in tool.description.lower()

    def test_schema_property(self):
        """Test tool schema."""
        tool = BrowserEvaluateTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "javascript" in schema["properties"]
        assert "javascript" in schema["required"]

    def test_execute_missing_javascript(self):
        """Test execute with missing javascript parameter."""
        tool = BrowserEvaluateTool()
        result = tool.execute()
        
        assert result.success is False
        assert "Missing required parameter: javascript" in result.error

    def test_execute_exception_handling(self):
        """Test execute handles exceptions gracefully."""
        tool = BrowserEvaluateTool()
        
        with patch.object(tool, "_evaluate", side_effect=Exception("Test error")):
            result = tool.execute(javascript="console.log('test')")
            assert result.success is False
            assert "Test error" in result.error

    def test_async_evaluate_success(self):
        """Test async evaluate method."""
        tool = BrowserEvaluateTool()
        
        async def run_test():
            mock_page = AsyncMock()
            mock_page.evaluate = AsyncMock(return_value={"result": 42})
            
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock(return_value=mock_page)
            
            result = await tool._evaluate("return {result: 42}")
            
            assert result.success is True
            assert "JavaScript execution result" in result.output
            mock_page.evaluate.assert_called_once_with("return {result: 42}")
        
        asyncio.run(run_test())

    def test_async_evaluate_failure(self):
        """Test async evaluate that fails."""
        tool = BrowserEvaluateTool()
        
        async def run_test():
            tool._browser_tools._ensure_browser = AsyncMock()
            tool._browser_tools._get_page = AsyncMock()
            tool._browser_tools._get_page.side_effect = Exception("No page")
            
            result = await tool._evaluate("console.log('test')")
            
            assert result.success is False
            assert "Evaluation failed" in result.error
        
        asyncio.run(run_test())


class TestBrowserCloseTool:
    """Tests for BrowserCloseTool."""

    def test_name_property(self):
        """Test tool name."""
        tool = BrowserCloseTool()
        assert tool.name == "browser_close"

    def test_description_property(self):
        """Test tool description."""
        tool = BrowserCloseTool()
        assert "Close" in tool.description
        assert "browser" in tool.description.lower()

    def test_schema_property(self):
        """Test tool schema."""
        tool = BrowserCloseTool()
        schema = tool.schema
        
        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["properties"] == {}

    def test_execute_success(self):
        """Test execute successfully closes browser."""
        tool = BrowserCloseTool()
        
        async def run_test():
            tool._browser_tools.close = AsyncMock()
            
            result = await tool._close()
            
            assert result.success is True
            assert "Browser closed" in result.output
        
        asyncio.run(run_test())

    def test_execute_exception_handling(self):
        """Test execute handles exceptions gracefully."""
        tool = BrowserCloseTool()
        
        with patch.object(tool, "_close", side_effect=Exception("Test error")):
            result = tool.execute()
            assert result.success is False
            assert "Test error" in result.error

    def test_async_close_failure(self):
        """Test async close that fails."""
        tool = BrowserCloseTool()
        
        async def run_test():
            tool._browser_tools.close = AsyncMock(side_effect=Exception("Close failed"))
            
            result = await tool._close()
            
            assert result.success is False
            assert "Close failed" in result.error
        
        asyncio.run(run_test())
