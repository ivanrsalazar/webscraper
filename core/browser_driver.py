#!/usr/bin/env python3
"""Browser automation driver with Playwright stealth mode."""
import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from playwright_stealth import stealth_async


class BrowserDriver:
    """
    Abstraction over Playwright browser automation.

    Features:
    - Stealth mode to hide automation
    - Cookie management
    - User agent control
    - Configurable headless/headful mode
    """

    def __init__(
        self,
        headless: bool = True,
        user_agent: Optional[str] = None,
        viewport: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize browser driver.

        Args:
            headless: Run browser in headless mode (default: True)
            user_agent: Custom user agent string (default: None = use default)
            viewport: Custom viewport size dict with 'width' and 'height' (default: 1920x1080)
        """
        self.headless = headless
        self.user_agent = user_agent
        self.viewport = viewport or {'width': 1920, 'height': 1080}

        # Playwright instances
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self) -> None:
        """
        Start browser instance.

        Initializes Playwright, launches browser with stealth settings,
        and creates a new page.
        """
        # Start Playwright
        self.playwright = await async_playwright().start()

        # Launch browser with anti-detection args
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--ignore-certificate-errors',
            ],
            # Use system DNS servers
            chromium_sandbox=False,
        )

        # Create context with custom settings
        context_options = {
            'viewport': self.viewport,
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
        }

        if self.user_agent:
            context_options['user_agent'] = self.user_agent

        self.context = await self.browser.new_context(**context_options)

        # Create page
        self.page = await self.context.new_page()

        # Apply stealth mode to hide automation
        await stealth_async(self.page)

    async def get(
        self,
        url: str,
        wait_until: str = 'networkidle',
        timeout: int = 30000
    ) -> str:
        """
        Navigate to URL and return page HTML.

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation complete
                       ('load', 'domcontentloaded', 'networkidle')
            timeout: Navigation timeout in milliseconds

        Returns:
            Page HTML content

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.page.goto(url, wait_until=wait_until, timeout=timeout)
        return await self.page.content()

    async def click(
        self,
        selector: str,
        timeout: int = 10000,
        wait_after: float = 1.0
    ) -> None:
        """
        Click an element.

        Args:
            selector: CSS selector for element to click
            timeout: Wait timeout in milliseconds
            wait_after: Seconds to wait after clicking (default: 1.0)

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.page.click(selector, timeout=timeout)
        if wait_after > 0:
            await asyncio.sleep(wait_after)

    async def fill(
        self,
        selector: str,
        value: str,
        timeout: int = 10000,
        clear_first: bool = True
    ) -> None:
        """
        Fill an input field.

        Args:
            selector: CSS selector for input element
            value: Value to fill
            timeout: Wait timeout in milliseconds
            clear_first: Clear field before filling (default: True)

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        if clear_first:
            await self.page.fill(selector, '', timeout=timeout)

        await self.page.fill(selector, value, timeout=timeout)

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int = 10000,
        state: str = 'visible'
    ) -> None:
        """
        Wait for an element to appear.

        Args:
            selector: CSS selector to wait for
            timeout: Wait timeout in milliseconds
            state: Element state to wait for ('visible', 'attached', 'hidden')

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.page.wait_for_selector(selector, timeout=timeout, state=state)

    async def scroll_to_bottom(self, delay: float = 0.5) -> None:
        """
        Scroll to bottom of page (useful for infinite scroll).

        Args:
            delay: Delay between scroll steps in seconds

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        previous_height = 0
        while True:
            # Scroll to bottom
            current_height = await self.page.evaluate('document.body.scrollHeight')

            if current_height == previous_height:
                # No more content to load
                break

            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(delay)
            previous_height = current_height

    async def get_cookies(self) -> List[Dict[str, Any]]:
        """
        Get all cookies from current context.

        Returns:
            List of cookie dictionaries

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.context:
            raise RuntimeError("Browser not started. Call start() first.")

        return await self.context.cookies()

    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """
        Set cookies in current context.

        Args:
            cookies: List of cookie dictionaries

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.context:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.context.add_cookies(cookies)

    async def screenshot(self, path: str, full_page: bool = False) -> None:
        """
        Take a screenshot of current page.

        Args:
            path: File path to save screenshot
            full_page: Capture full page (default: False = viewport only)

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.page.screenshot(path=path, full_page=full_page)

    async def evaluate(self, script: str) -> Any:
        """
        Execute JavaScript in page context.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of script execution

        Raises:
            RuntimeError: If browser is not started
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        return await self.page.evaluate(script)

    async def close(self) -> None:
        """
        Close browser and cleanup resources.
        """
        if self.page:
            await self.page.close()
            self.page = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def is_started(self) -> bool:
        """
        Check if browser is started.

        Returns:
            True if browser is started and ready, False otherwise
        """
        return self.page is not None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def __str__(self) -> str:
        """String representation."""
        status = "started" if self.is_started() else "stopped"
        mode = "headless" if self.headless else "headful"
        return f"BrowserDriver(status={status}, mode={mode})"
