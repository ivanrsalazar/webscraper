#!/usr/bin/env python3
"""
Main CLI entry point for the webscraper.

Usage:
    python main.py --site walmart --zipcode 94102 --query "laptop" --max-results 5
"""
import asyncio
import argparse
import yaml
import json
from pathlib import Path
from typing import List

from core.browser_driver import BrowserDriver
from core.user_agent import UserAgentRotator
from core.rate_limiter import RateLimiter
from core.session_manager import SessionManager
from scrapers.walmart_scraper import WalmartScraper
from models.product import Product
from utils.logger import setup_logger

logger = setup_logger('main', level='INFO')


def load_config(site: str) -> dict:
    """
    Load site configuration from YAML file.

    Args:
        site: Site name (e.g., 'walmart')

    Returns:
        Configuration dictionary
    """
    config_path = Path(__file__).parent / 'config' / 'sites' / f'{site}.yaml'

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


async def scrape_site(
    site: str,
    zipcode: str,
    query: str,
    max_results: int = 20,
    headless: bool = True
) -> List[Product]:
    """
    Scrape products from a site.

    Args:
        site: Site name (e.g., 'walmart')
        zipcode: 5-digit US zipcode
        query: Search query
        max_results: Maximum number of products to scrape
        headless: Run browser in headless mode

    Returns:
        List of scraped products
    """
    # Load configuration
    config = load_config(site)
    logger.info(f"Loaded configuration for {site}")

    # Initialize components
    ua_rotator = UserAgentRotator()
    user_agent = ua_rotator.get_for_site(site)

    browser = BrowserDriver(
        headless=headless,
        user_agent=user_agent
    )

    rate_limiter = RateLimiter(
        requests_per_minute=config['rate_limiting']['requests_per_minute'],
        min_delay=config['rate_limiting']['min_delay_seconds'],
        max_delay=config['rate_limiting']['max_delay_seconds']
    )

    session_manager = SessionManager()

    # Create scraper based on site
    if site == 'walmart':
        scraper = WalmartScraper(
            config=config,
            browser_driver=browser,
            rate_limiter=rate_limiter,
            session_manager=session_manager
        )
    else:
        raise ValueError(f"Unsupported site: {site}")

    products = []

    try:
        # Start browser
        await browser.start()
        logger.info("Browser started")

        # Set location
        success = await scraper.set_location(zipcode)
        if not success:
            logger.error(f"Failed to set location to {zipcode}")
            return products

        # Search for products
        product_urls = await scraper.search_products(query, max_results=max_results)
        logger.info(f"Found {len(product_urls)} product URLs")

        # Scrape product details
        for i, url in enumerate(product_urls, 1):
            logger.info(f"Scraping product {i}/{len(product_urls)}")
            product = await scraper.get_product_details(url)
            if product:
                products.append(product)

        logger.info(f"Successfully scraped {len(products)} products")

    except Exception as e:
        logger.error(f"Error during scraping: {e}")

    finally:
        # Cleanup
        await browser.close()
        logger.info("Browser closed")

    return products


def save_products(products: List[Product], output_file: str):
    """
    Save products to JSON file.

    Args:
        products: List of products
        output_file: Output file path
    """
    data = [p.to_dict() for p in products]

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved {len(products)} products to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Multi-site retail webscraper for product pricing'
    )

    parser.add_argument(
        '--site',
        required=True,
        choices=['walmart'],
        help='Site to scrape'
    )

    parser.add_argument(
        '--zipcode',
        required=True,
        help='5-digit US zipcode'
    )

    parser.add_argument(
        '--query',
        required=True,
        help='Product search query'
    )

    parser.add_argument(
        '--max-results',
        type=int,
        default=5,
        help='Maximum number of products to scrape (default: 5)'
    )

    parser.add_argument(
        '--output',
        default='products.json',
        help='Output file path (default: products.json)'
    )

    parser.add_argument(
        '--headful',
        action='store_true',
        help='Run browser in headful mode (visible, not headless)'
    )

    args = parser.parse_args()

    # Run scraper
    logger.info("="*80)
    logger.info(f"Starting scraper: site={args.site}, zipcode={args.zipcode}, query='{args.query}'")
    logger.info("="*80)

    products = asyncio.run(scrape_site(
        site=args.site,
        zipcode=args.zipcode,
        query=args.query,
        max_results=args.max_results,
        headless=not args.headful
    ))

    # Save results
    if products:
        save_products(products, args.output)
        logger.info("="*80)
        logger.info(f"Scraping complete! Found {len(products)} products")
        logger.info("="*80)

        # Print summary
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product.name}")
            print(f"   Price: ${product.current_price:.2f}" if product.current_price else "   Price: N/A")
            print(f"   In Stock: {product.in_stock}")
            print(f"   URL: {product.url}")
    else:
        logger.warning("No products were scraped")


if __name__ == '__main__':
    main()
