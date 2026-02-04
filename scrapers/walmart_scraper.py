#!/usr/bin/env python3
"""Walmart-specific scraper implementation."""
import asyncio
from typing import List, Optional
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base_scraper import BaseScraper
from models.product import Product
from parsers.selector_engine import SelectorEngine
from utils.normalizers import normalize_price, parse_availability, normalize_rating
from utils.logger import setup_logger

logger = setup_logger('walmart_scraper', level='INFO')


class WalmartScraper(BaseScraper):
    """
    Walmart-specific scraper implementation.

    Features:
    - Cookie-based location setting
    - Product search with "Load More" pagination
    - Full product detail extraction
    """

    async def set_location(self, zipcode: str) -> bool:
        """
        Set location using Walmart's location modal.

        Args:
            zipcode: 5-digit US zipcode

        Returns:
            True if location was successfully set
        """
        try:
            logger.info(f"[Walmart] Setting location to zipcode: {zipcode}")

            # Check rate limit
            if self.rate_limiter:
                await self.rate_limiter.acquire('walmart')

            # Check for existing session
            if self.session_manager:
                cookies = self.session_manager.get_cookies('walmart', zipcode)
                if cookies:
                    logger.info(f"[Walmart] Restored session from cache for {zipcode}")
                    await self.browser_driver.set_cookies(cookies)
                    self.current_zipcode = zipcode
                    return True

            # Navigate to Walmart homepage
            await self.browser_driver.get('https://www.walmart.com', wait_until='load')
            await asyncio.sleep(2)  # Let page settle

            # Find and click location button
            location_buttons = self.config['location']['selectors']['location_button']
            clicked = False

            for selector in location_buttons:
                try:
                    await self.browser_driver.click(selector, timeout=5000)
                    clicked = True
                    logger.info(f"[Walmart] Clicked location button: {selector}")
                    break
                except Exception:
                    continue

            if not clicked:
                logger.error("[Walmart] Failed to find/click location button")
                return False

            # Wait for modal to appear
            await asyncio.sleep(2)

            # Find and fill zipcode input
            zipcode_inputs = self.config['location']['selectors']['zipcode_input']
            filled = False

            for selector in zipcode_inputs:
                try:
                    await self.browser_driver.fill(selector, zipcode, timeout=5000)
                    filled = True
                    logger.info(f"[Walmart] Filled zipcode input: {selector}")
                    break
                except Exception:
                    continue

            if not filled:
                logger.error("[Walmart] Failed to find/fill zipcode input")
                return False

            # Click submit button
            submit_buttons = self.config['location']['selectors']['submit_button']
            submitted = False

            for selector in submit_buttons:
                try:
                    await self.browser_driver.click(selector, timeout=5000)
                    submitted = True
                    logger.info(f"[Walmart] Clicked submit button: {selector}")
                    break
                except Exception:
                    continue

            if not submitted:
                logger.error("[Walmart] Failed to find/click submit button")
                return False

            # Wait for location update
            await asyncio.sleep(3)

            # Save cookies for session reuse
            if self.session_manager:
                cookies = await self.browser_driver.get_cookies()
                self.session_manager.save_session('walmart', zipcode, cookies)
                logger.info(f"[Walmart] Saved session for {zipcode}")

            self.current_zipcode = zipcode
            logger.info(f"[Walmart] Successfully set location to {zipcode}")
            return True

        except Exception as e:
            logger.error(f"[Walmart] Error setting location: {e}")
            return False

    async def search_products(
        self,
        query: str,
        max_results: int = 20,
        **kwargs
    ) -> List[str]:
        """
        Search for products and return product URLs.

        Args:
            query: Search query
            max_results: Maximum number of product URLs to return

        Returns:
            List of product page URLs
        """
        try:
            logger.info(f"[Walmart] Searching for: {query} (max: {max_results})")

            # Check rate limit
            if self.rate_limiter:
                await self.rate_limiter.acquire('walmart')

            # Build search URL
            search_url = self.config['search']['url_template'].format(
                query=query.replace(' ', '+'),
                page=1
            )

            # Navigate to search page
            await self.browser_driver.get(search_url, wait_until='networkidle')
            await asyncio.sleep(2)

            product_urls = []

            # Extract product links
            product_card_selectors = self.config['search']['selectors']['product_cards']
            product_link_selectors = self.config['search']['selectors']['product_link']

            html = await self.browser_driver.page.content()
            engine = SelectorEngine(html)

            # Find product links
            links = engine.select_many(product_link_selectors, attr='href', limit=max_results)

            for link in links:
                # Make absolute URL
                if link.startswith('/'):
                    link = 'https://www.walmart.com' + link
                product_urls.append(link)

            logger.info(f"[Walmart] Found {len(product_urls)} product URLs")
            return product_urls[:max_results]

        except Exception as e:
            logger.error(f"[Walmart] Error searching products: {e}")
            return []

    async def get_product_details(self, product_url: str) -> Optional[Product]:
        """
        Get full product details from a product page.

        Args:
            product_url: Product page URL

        Returns:
            Product object with all scraped details
        """
        try:
            logger.info(f"[Walmart] Fetching product: {product_url}")

            # Check rate limit
            if self.rate_limiter:
                await self.rate_limiter.acquire('walmart')

            # Navigate to product page
            await self.browser_driver.get(product_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # Get HTML content
            html = await self.browser_driver.page.content()

            # Parse product
            product = self.parse_product(html, product_url)

            if product:
                logger.info(f"[Walmart] Scraped: {product.name} - ${product.current_price}")
            else:
                logger.warning(f"[Walmart] Failed to parse product from {product_url}")

            return product

        except Exception as e:
            logger.error(f"[Walmart] Error fetching product details: {e}")
            return None

    def parse_product(self, html: str, url: str) -> Optional[Product]:
        """
        Parse product data from HTML.

        Args:
            html: HTML content of product page
            url: Product URL

        Returns:
            Product object or None if parsing failed
        """
        try:
            engine = SelectorEngine(html)
            selectors = self.config['product']['selectors']

            # Extract product name (required)
            name = engine.select_one(selectors['name'])
            if not name:
                logger.warning("[Walmart] Failed to extract product name")
                return None

            # Extract prices
            current_price_str = engine.select_one(selectors['current_price'])
            original_price_str = engine.select_one(selectors['original_price'])

            current_price = normalize_price(current_price_str)
            original_price = normalize_price(original_price_str)

            # Calculate discount if applicable
            discount_percent = None
            if current_price and original_price and original_price > current_price:
                discount_percent = ((original_price - current_price) / original_price) * 100

            # Extract availability
            stock_status_text = engine.select_one(selectors['stock_status'])
            availability = parse_availability(stock_status_text)

            # Extract ratings
            rating_avg_str = engine.select_one(selectors['rating_avg'])
            rating_count_str = engine.select_one(selectors['rating_count'])

            rating_avg = normalize_rating(rating_avg_str)
            rating_count = None
            if rating_count_str:
                import re
                match = re.search(r'(\d+)', rating_count_str)
                if match:
                    rating_count = int(match.group(1))

            # Extract shipping info
            free_shipping_text = engine.select_one(selectors['free_shipping'])
            free_shipping = free_shipping_text is not None and 'free' in free_shipping_text.lower()

            delivery_date = engine.select_one(selectors['delivery_date'])

            # Extract product details
            brand = engine.select_one(selectors['brand'])
            model = engine.select_one(selectors['model'])
            description = engine.select_one(selectors['description'])

            # Extract specifications table
            specs = engine.extract_table(selectors['specs_table'])

            # Extract images
            image_urls = engine.select_many(selectors['images'], attr='src', limit=5)

            # Create product object
            product = Product(
                name=name,
                url=url,
                site='walmart',
                zipcode=self.current_zipcode or 'unknown',
                scraped_at=datetime.now(),
                current_price=current_price,
                original_price=original_price,
                discount_percent=discount_percent,
                in_stock=availability['in_stock'],
                quantity_available=availability.get('quantity'),
                stock_status_text=stock_status_text,
                rating_avg=rating_avg,
                rating_count=rating_count,
                free_shipping=free_shipping,
                delivery_date=delivery_date,
                brand=brand,
                model=model,
                description=description,
                specs=specs if specs else None,
                image_urls=image_urls if image_urls else None,
                primary_image_url=image_urls[0] if image_urls else None,
            )

            # Validate product
            if not product.validate():
                logger.warning(f"[Walmart] Product validation failed for {url}")

            return product

        except Exception as e:
            logger.error(f"[Walmart] Error parsing product: {e}")
            return None
