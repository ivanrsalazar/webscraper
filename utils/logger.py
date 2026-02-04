#!/usr/bin/env python3
"""Structured logging setup for webscraper."""
import logging
import sys
from typing import Any, Dict


def setup_logger(name: str = 'scraper', level: str = 'INFO') -> logging.Logger:
    """
    Set up a logger with structured output.

    Args:
        name: Logger name
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def log_scrape_event(
    logger: logging.Logger,
    event_type: str,
    site: str,
    zipcode: str = None,
    **kwargs: Any
) -> None:
    """
    Log a scraping event with structured data.

    Args:
        logger: Logger instance
        event_type: Type of event (e.g., 'product_scraped', 'location_set', 'error')
        site: Site name
        zipcode: Optional zipcode
        **kwargs: Additional key-value pairs to log
    """
    # Build log message
    parts = [f"[{site}]"]
    if zipcode:
        parts.append(f"[{zipcode}]")
    parts.append(event_type)

    # Add kwargs as key=value pairs
    if kwargs:
        details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        parts.append(f"| {details}")

    message = " ".join(parts)
    logger.info(message)


# Create default logger
default_logger = setup_logger()
