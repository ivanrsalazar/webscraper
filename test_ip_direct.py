#!/usr/bin/env python3
"""Test direct IP access."""
import asyncio
from playwright.async_api import async_playwright


async def test_direct_ip():
    """Test accessing Walmart via IP address."""
    print("Testing direct IP access...")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()

        # Walmart IP from your DNS test: 23.205.156.171
        # Add Host header to make it work
        await page.set_extra_http_headers({
            'Host': 'www.walmart.com'
        })

        print("Navigating to http://23.205.156.171...")
        try:
            await page.goto('http://23.205.156.171/', timeout=15000)
            print(f"✓ Success! Title: {await page.title()}")
        except Exception as e:
            print(f"✗ Failed: {e}")

        await browser.close()


if __name__ == '__main__':
    asyncio.run(test_direct_ip())
