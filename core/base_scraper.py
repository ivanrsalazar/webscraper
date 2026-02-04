#!/usr/bin/env python3
"""Abstract base class for all site-specific scrapers."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models.product import Product


class BaseScraper(ABC):
    """
    Abstract base class defining the interface for all site-specific scrapers.

    All concrete scraper implementations (WalmartScraper, TargetScraper, etc.)
    must inherit from this class and implement the abstract methods.

    Attributes:
        site_name: Name of the site (e.g., 'walmart', 'target')
        config: Site-specific configuration loaded from YAML
        browser_driver: Browser automation driver
        location_manager: Handles location/zipcode setting
        session_manager: Manages cookies and sessions
        rate_limiter: Controls request rate
        cache_manager: Caches responses
    """

    def __init__(
        self,
        config: Dict[str, Any],
        browser_driver: Any = None,
        location_manager: Any = None,
        session_manager: Any = None,
        rate_limiter: Any = None,
        cache_manager: Any = None,
    ):
        """
        Initialize base scraper with dependencies.

        Args:
            config: Site-specific configuration dictionary
            browser_driver: Browser automation driver instance
            location_manager: Location manager instance
            session_manager: Session manager instance
            rate_limiter: Rate limiter instance
            cache_manager: Cache manager instance
        """
        self.site_name = config.get('site', {}).get('name', 'unknown')
        self.config = config
        self.browser_driver = browser_driver
        self.location_manager = location_manager
        self.session_manager = session_manager
        self.rate_limiter = rate_limiter
        self.cache_manager = cache_manager
        self.current_zipcode: Optional[str] = None

    @abstractmethod
    async def set_location(self, zipcode: str) -> bool:
        """
        Set the location/zipcode for product search.

        Different sites use different methods:
        - Walmart: Cookie-based location modal
        - Target: URL parameter + API call
        - Others: Custom implementation

        Args:
            zipcode: 5-digit US zipcode

        Returns:
            True if location was successfully set, False otherwise

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclass must implement set_location()")

    @abstractmethod
    async def search_products(
        self,
        query: str,
        max_results: int = 20,
        **kwargs
    ) -> List[str]:
        """
        Search for products and return list of product URLs.

        Args:
            query: Search query string
            max_results: Maximum number of product URLs to return
            **kwargs: Additional site-specific parameters

        Returns:
            List of product URLs

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclass must implement search_products()")

    @abstractmethod
    async def get_product_details(self, product_url: str) -> Optional[Product]:
        """
        Get full product details from a product page URL.

        Args:
            product_url: Full URL to product page

        Returns:
            Product object with all scraped details, or None if scraping failed

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclass must implement get_product_details()")

    @abstractmethod
    def parse_product(self, html: str, url: str) -> Optional[Product]:
        """
        Parse product data from HTML content.

        Args:
            html: HTML content of product page
            url: URL of the product page

        Returns:
            Product object with parsed data, or None if parsing failed

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclass must implement parse_product()")

    async def validate_location(self, expected_zipcode: str) -> bool:
        """
        Validate that the location was set correctly.

        This method can be overridden by subclasses for custom validation.
        Default implementation checks if current_zipcode matches expected.

        Args:
            expected_zipcode: The zipcode that should be set

        Returns:
            True if location is correctly set, False otherwise
        """
        return self.current_zipcode == expected_zipcode

    def get_site_name(self) -> str:
        """
        Get the name of the site this scraper handles.

        Returns:
            Site name (e.g., 'walmart', 'target')
        """
        return self.site_name

    def get_config(self) -> Dict[str, Any]:
        """
        Get the full configuration for this scraper.

        Returns:
            Configuration dictionary
        """
        return self.config

    async def cleanup(self):
        """
        Cleanup resources (close browser, save sessions, etc.).

        Can be overridden by subclasses for custom cleanup logic.
        """
        if self.browser_driver:
            await self.browser_driver.close()

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(site='{self.site_name}')"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"{self.__class__.__name__}(site='{self.site_name}', "
            f"zipcode='{self.current_zipcode}')"
        )
