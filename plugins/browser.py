"""
Playwright Browser Plugin for JARVIS

Provides the agent with the ability to control a headless web browser.
"""
from playwright.async_api import async_playwright
from core.logger import get_logger

logger = get_logger("plugin.browser")

# Global browser instance
_browser = None
_context = None
_page = None
_playwright = None

async def _ensure_browser():
    global _playwright, _browser, _context, _page
    if not _playwright:
        _playwright = await async_playwright().start()
        # Note: headless=False can be used if the user wants to watch JARVIS automate the web!
        _browser = await _playwright.chromium.launch(headless=True)
        _context = await _browser.new_context()
        _page = await _context.new_page()

def register(brain, settings):
    """Register browser tools."""
    
    async def navigate(url: str) -> str:
        """Navigates the browser to a specific URL and returns the page text."""
        await _ensure_browser()
        try:
            # Ensure proper URL format
            if not url.startswith("http"):
                url = f"https://{url}"
                
            await _page.goto(url, wait_until="networkidle")
            text = await _page.evaluate("document.body.innerText")
            if len(text) > 4000:
                text = text[:4000] + "\n...[CONTENT TRUNCATED]..."
            return f"Navigated to {url}. Page content:\n{text}"
        except Exception as e:
            return f"Failed to navigate: {e}"

    async def click(selector: str) -> str:
        """Clicks an element on the page matching the CSS selector."""
        await _ensure_browser()
        try:
            await _page.click(selector)
            # Give page time to load new content
            await _page.wait_for_load_state("networkidle", timeout=3000)
            return f"Clicked element: {selector}"
        except Exception as e:
            return f"Failed to click {selector}: {e}"
            
    async def fill_text(selector: str, text: str) -> str:
        """Fills an input field matching the CSS selector with text."""
        await _ensure_browser()
        try:
            await _page.fill(selector, text)
            return f"Filled {selector} with '{text}'"
        except Exception as e:
            return f"Failed to fill {selector}: {e}"
            
    brain.register_tool(
        name="browser_navigate",
        description="Navigates a headless browser to a URL and returns the text content. Use this to read web pages, search Google, or access web apps.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The full URL to navigate to (e.g. 'https://duckduckgo.com')"}
            },
            "required": ["url"]
        },
        handler=navigate
    )
    
    brain.register_tool(
        name="browser_click",
        description="Clicks an HTML element using a CSS selector (e.g., 'button#submit' or '.search-result a').",
        parameters={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the element to click."}
            },
            "required": ["selector"]
        },
        handler=click
    )
    
    brain.register_tool(
        name="browser_fill_text",
        description="Types text into an input field using a CSS selector.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the input field."},
                "text": {"type": "string", "description": "The text to type into the field."}
            },
            "required": ["selector", "text"]
        },
        handler=fill_text
    )
    
    logger.info("Browser plugin registered.")
