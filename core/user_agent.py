#!/usr/bin/env python3
"""User agent rotation for avoiding bot detection."""
import random
from typing import Optional


class UserAgentRotator:
    """
    Rotates user agents to avoid bot detection.

    Maintains a pool of realistic user agents from popular browsers
    (Chrome, Firefox, Safari, Edge) across different operating systems.
    """

    # Pool of realistic user agents (Chrome, Firefox, Safari, Edge)
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",

        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",

        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",

        # Firefox on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",

        # Firefox on Linux
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",

        # Safari on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",

        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",

        # Edge on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    # Site-specific user agent preferences
    SITE_PREFERENCES = {
        'walmart': 'chrome',  # Walmart works well with Chrome
        'target': 'chrome',
        'bestbuy': 'chrome',
        'amazon': 'firefox',
    }

    def __init__(self):
        """Initialize user agent rotator."""
        self.last_used = None

    def get_random(self) -> str:
        """
        Get a random user agent from the pool.

        Returns:
            Random user agent string
        """
        ua = random.choice(self.USER_AGENTS)
        self.last_used = ua
        return ua

    def get_for_site(self, site: str) -> str:
        """
        Get a user agent optimized for a specific site.

        Args:
            site: Site name (e.g., 'walmart', 'target')

        Returns:
            User agent string suitable for the site
        """
        preference = self.SITE_PREFERENCES.get(site.lower())

        if preference == 'chrome':
            # Filter to Chrome user agents
            chrome_agents = [ua for ua in self.USER_AGENTS if 'Chrome/' in ua and 'Edg/' not in ua]
            ua = random.choice(chrome_agents)
        elif preference == 'firefox':
            # Filter to Firefox user agents
            firefox_agents = [ua for ua in self.USER_AGENTS if 'Firefox/' in ua]
            ua = random.choice(firefox_agents)
        else:
            # Default to random
            ua = self.get_random()

        self.last_used = ua
        return ua

    def get_last_used(self) -> Optional[str]:
        """
        Get the last used user agent.

        Returns:
            Last used user agent string, or None if none has been used yet
        """
        return self.last_used

    def get_browser_type(self, user_agent: str) -> str:
        """
        Determine browser type from user agent string.

        Args:
            user_agent: User agent string

        Returns:
            Browser type ('chrome', 'firefox', 'safari', 'edge', 'unknown')
        """
        if 'Edg/' in user_agent:
            return 'edge'
        elif 'Chrome/' in user_agent:
            return 'chrome'
        elif 'Firefox/' in user_agent:
            return 'firefox'
        elif 'Safari/' in user_agent and 'Chrome/' not in user_agent:
            return 'safari'
        else:
            return 'unknown'

    def __str__(self) -> str:
        """String representation."""
        return f"UserAgentRotator(pool_size={len(self.USER_AGENTS)})"
