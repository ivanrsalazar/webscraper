#!/usr/bin/env python3
"""Rate limiter for controlling request frequency."""
import asyncio
import random
import time
from typing import Dict, Optional
from datetime import datetime, timedelta


class RateLimiter:
    """
    Token bucket rate limiter with per-site quotas.

    Features:
    - Per-site request limits (e.g., 10 req/min for Walmart)
    - Automatic backoff on rate limit errors (429/503)
    - Randomized delays to mimic human behavior
    - Token bucket algorithm for smooth rate limiting
    """

    def __init__(
        self,
        requests_per_minute: int = 10,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay between requests in seconds
        """
        self.requests_per_minute = requests_per_minute
        self.min_delay = min_delay
        self.max_delay = max_delay

        # Token bucket state per site
        self.tokens: Dict[str, float] = {}
        self.last_refill: Dict[str, datetime] = {}

        # Backoff state per site
        self.backoff_multiplier: Dict[str, float] = {}
        self.last_request_time: Dict[str, float] = {}

    def _refill_tokens(self, site: str) -> None:
        """
        Refill tokens based on time elapsed since last refill.

        Args:
            site: Site name to refill tokens for
        """
        now = datetime.now()

        # Initialize if first request
        if site not in self.last_refill:
            self.tokens[site] = float(self.requests_per_minute)
            self.last_refill[site] = now
            return

        # Calculate tokens to add based on time elapsed
        elapsed = (now - self.last_refill[site]).total_seconds()
        tokens_to_add = (elapsed / 60.0) * self.requests_per_minute

        # Add tokens (capped at max)
        self.tokens[site] = min(
            self.tokens[site] + tokens_to_add,
            float(self.requests_per_minute)
        )
        self.last_refill[site] = now

    async def acquire(self, site: str) -> None:
        """
        Wait until a request is allowed for the given site.

        This method will:
        1. Refill tokens if enough time has passed
        2. Wait if no tokens are available
        3. Add a random delay to mimic human behavior
        4. Apply backoff multiplier if needed

        Args:
            site: Site name to acquire rate limit token for
        """
        # Refill tokens
        self._refill_tokens(site)

        # Wait if no tokens available
        while self.tokens.get(site, 0) < 1.0:
            wait_time = 1.0  # Wait 1 second and check again
            await asyncio.sleep(wait_time)
            self._refill_tokens(site)

        # Consume one token
        self.tokens[site] -= 1.0

        # Calculate delay with backoff
        base_delay = random.uniform(self.min_delay, self.max_delay)
        backoff = self.backoff_multiplier.get(site, 1.0)
        total_delay = base_delay * backoff

        # Ensure minimum time since last request
        if site in self.last_request_time:
            time_since_last = time.time() - self.last_request_time[site]
            if time_since_last < total_delay:
                additional_wait = total_delay - time_since_last
                await asyncio.sleep(additional_wait)
        else:
            await asyncio.sleep(total_delay)

        # Record request time
        self.last_request_time[site] = time.time()

    def trigger_backoff(self, site: str, multiplier: float = 2.0) -> None:
        """
        Increase delays temporarily after hitting rate limits.

        This is typically called when receiving 429 (Too Many Requests)
        or 503 (Service Unavailable) responses.

        Args:
            site: Site name to apply backoff to
            multiplier: Factor to multiply delays by (default: 2.0)
        """
        current_backoff = self.backoff_multiplier.get(site, 1.0)
        self.backoff_multiplier[site] = min(current_backoff * multiplier, 10.0)

    def reset_backoff(self, site: str) -> None:
        """
        Reset backoff multiplier to normal after successful requests.

        Args:
            site: Site name to reset backoff for
        """
        self.backoff_multiplier[site] = 1.0

    def get_current_rate(self, site: str) -> float:
        """
        Get current request rate for a site.

        Args:
            site: Site name

        Returns:
            Requests per minute based on current token count
        """
        tokens = self.tokens.get(site, self.requests_per_minute)
        return tokens

    def get_backoff_multiplier(self, site: str) -> float:
        """
        Get current backoff multiplier for a site.

        Args:
            site: Site name

        Returns:
            Current backoff multiplier
        """
        return self.backoff_multiplier.get(site, 1.0)

    def is_rate_limited(self, site: str) -> bool:
        """
        Check if site is currently rate limited (no tokens available).

        Args:
            site: Site name

        Returns:
            True if rate limited, False otherwise
        """
        self._refill_tokens(site)
        return self.tokens.get(site, 0) < 1.0

    def get_wait_time(self, site: str) -> float:
        """
        Get estimated wait time before next request is allowed.

        Args:
            site: Site name

        Returns:
            Estimated wait time in seconds
        """
        self._refill_tokens(site)
        tokens = self.tokens.get(site, 0)

        if tokens >= 1.0:
            return 0.0

        # Calculate time needed to refill one token
        tokens_needed = 1.0 - tokens
        seconds_per_token = 60.0 / self.requests_per_minute
        return tokens_needed * seconds_per_token

    def __str__(self) -> str:
        """String representation."""
        return (
            f"RateLimiter(rpm={self.requests_per_minute}, "
            f"delay={self.min_delay}-{self.max_delay}s)"
        )
