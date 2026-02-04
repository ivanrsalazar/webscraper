#!/usr/bin/env python3
"""Test script to diagnose network/DNS issues."""
import asyncio
import socket
from playwright.async_api import async_playwright


async def test_dns():
    """Test if DNS resolution works."""
    print("Testing DNS resolution...")
    try:
        result = socket.gethostbyname('walmart.com')
        print(f"✓ DNS works: walmart.com = {result}")
        return True
    except socket.gaierror as e:
        print(f"✗ DNS failed: {e}")
        return False


async def test_playwright_chromium():
    """Test if Playwright Chromium can connect."""
    print("\nTesting Playwright Chromium...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-web-security']
            )
            page = await browser.new_page()

            # Try to navigate
            print("Attempting to navigate to walmart.com...")
            await page.goto('https://www.walmart.com/', timeout=15000)
            title = await page.title()
            print(f"✓ Chromium works: Page title = {title}")
            await browser.close()
            return True
    except Exception as e:
        print(f"✗ Chromium failed: {e}")
        return False


async def test_playwright_firefox():
    """Test if Playwright Firefox can connect."""
    print("\nTesting Playwright Firefox...")
    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()

            print("Attempting to navigate to walmart.com...")
            await page.goto('https://www.walmart.com/', timeout=15000)
            title = await page.title()
            print(f"✓ Firefox works: Page title = {title}")
            await browser.close()
            return True
    except Exception as e:
        print(f"✗ Firefox failed: {e}")
        return False


async def main():
    print("="*60)
    print("Network Connectivity Test")
    print("="*60)

    # Test DNS
    dns_works = await test_dns()

    # Test Playwright browsers
    chromium_works = await test_playwright_chromium()

    # Only test Firefox if installed
    # firefox_works = await test_playwright_firefox()

    print("\n" + "="*60)
    print("Summary:")
    print(f"DNS Resolution: {'✓ Working' if dns_works else '✗ Failed'}")
    print(f"Playwright Chromium: {'✓ Working' if chromium_works else '✗ Failed'}")
    print("="*60)

    if not dns_works:
        print("\n⚠ DNS is not working on this system.")
        print("This is a system-level issue, not a scraper issue.")
    elif not chromium_works:
        print("\n⚠ DNS works but Playwright Chromium cannot connect.")
        print("Try installing Firefox: playwright install firefox")


if __name__ == '__main__':
    asyncio.run(main())
