#!/usr/bin/env python3
"""Data normalization utilities for product data."""
import re
from typing import Optional, Dict


def normalize_price(price_str: Optional[str]) -> Optional[float]:
    """
    Normalize price string to float.

    Handles various formats:
    - $19.99 → 19.99
    - $1,299.00 → 1299.00
    - 19.99 USD → 19.99
    - $19.99 - $29.99 → 19.99 (take minimum)

    Args:
        price_str: Price string to normalize

    Returns:
        Normalized price as float, or None if invalid
    """
    if not price_str:
        return None

    # Remove currency symbols and commas
    clean = re.sub(r'[$,]', '', str(price_str))

    # Handle ranges (take minimum)
    if '-' in clean:
        prices = clean.split('-')
        clean = prices[0].strip()

    # Extract first number (handles "19.99 USD" etc.)
    match = re.search(r'\d+\.?\d*', clean)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None

    return None


def parse_availability(status_text: Optional[str]) -> Dict[str, any]:
    """
    Parse availability status text into structured data.

    Args:
        status_text: Availability status text

    Returns:
        Dictionary with:
            - in_stock: bool
            - quantity: Optional[int]
            - status: str ('in_stock', 'out_of_stock', 'limited')
    """
    if not status_text:
        return {'in_stock': None, 'quantity': None, 'status': 'unknown'}

    status_lower = status_text.lower()

    # Check for out of stock
    if any(x in status_lower for x in ['out of stock', 'unavailable', 'sold out']):
        return {'in_stock': False, 'quantity': 0, 'status': 'out_of_stock'}

    # Check for limited stock with quantity
    if 'limited' in status_lower or 'only' in status_lower:
        # Try to extract quantity: "Only 3 left", "Limited: 5 available"
        match = re.search(r'(\d+)', status_text)
        qty = int(match.group(1)) if match else None
        return {'in_stock': True, 'quantity': qty, 'status': 'limited'}

    # Default to in stock
    return {'in_stock': True, 'quantity': None, 'status': 'in_stock'}


def normalize_rating(rating_str: Optional[str]) -> Optional[float]:
    """
    Normalize rating string to float (0-5 scale).

    Args:
        rating_str: Rating string (e.g., "4.5", "4.5 out of 5", "4.5/5")

    Returns:
        Normalized rating as float, or None if invalid
    """
    if not rating_str:
        return None

    # Extract number
    match = re.search(r'(\d+\.?\d*)', str(rating_str))
    if match:
        try:
            rating = float(match.group(1))
            # Validate 0-5 range
            if 0 <= rating <= 5:
                return rating
        except ValueError:
            pass

    return None
