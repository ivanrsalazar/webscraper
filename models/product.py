#!/usr/bin/env python3
"""Product data model for webscraper."""
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class Product:
    """
    Product data model representing scraped product information.

    Core fields are required, optional fields may be None if not available
    from the source website.
    """

    # Core required fields
    name: str
    url: str
    site: str
    zipcode: str
    scraped_at: datetime = field(default_factory=datetime.now)

    # Pricing information
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    currency: str = "USD"

    # Availability
    in_stock: Optional[bool] = None
    quantity_available: Optional[int] = None
    stock_status_text: Optional[str] = None

    # Ratings & Reviews
    rating_avg: Optional[float] = None
    rating_count: Optional[int] = None
    review_summary: Optional[str] = None

    # Shipping information
    shipping_cost: Optional[float] = None
    free_shipping: Optional[bool] = None
    delivery_date: Optional[str] = None
    delivery_days: Optional[int] = None

    # Product details
    brand: Optional[str] = None
    model: Optional[str] = None
    upc: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    specs: Optional[Dict[str, str]] = None
    description: Optional[str] = None

    # Images
    image_urls: Optional[List[str]] = None
    primary_image_url: Optional[str] = None

    # Metadata
    product_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """
        Convert product to dictionary.

        Returns:
            Dictionary representation of product with datetime serialized.
        """
        data = asdict(self)
        # Serialize datetime
        data['scraped_at'] = self.scraped_at.isoformat()
        return data

    def validate(self) -> bool:
        """
        Validate that required fields are present and valid.

        Returns:
            True if product has all required fields with valid values.
        """
        # Check required fields
        if not self.name or not self.url or not self.site or not self.zipcode:
            return False

        # Validate price if present
        if self.current_price is not None and self.current_price < 0:
            return False

        if self.original_price is not None and self.original_price < 0:
            return False

        # Validate rating if present
        if self.rating_avg is not None and not (0 <= self.rating_avg <= 5):
            return False

        if self.rating_count is not None and self.rating_count < 0:
            return False

        # Validate quantity if present
        if self.quantity_available is not None and self.quantity_available < 0:
            return False

        return True

    def __str__(self) -> str:
        """String representation of product."""
        price_str = f"${self.current_price:.2f}" if self.current_price else "N/A"
        stock_str = "In Stock" if self.in_stock else "Out of Stock" if self.in_stock is False else "Unknown"
        return f"{self.name} - {price_str} ({stock_str}) [{self.site}]"

    def __repr__(self) -> str:
        """Detailed representation of product."""
        return (
            f"Product(name='{self.name}', price={self.current_price}, "
            f"site='{self.site}', zipcode='{self.zipcode}')"
        )


@dataclass
class ScrapeResult:
    """
    Container for scrape results with metadata.

    Used to return scraped products along with success/error information.
    """

    site: str
    zipcode: str
    query: Optional[str] = None
    products: List[Product] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    products_found: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Update products_found count."""
        self.products_found = len(self.products)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'site': self.site,
            'zipcode': self.zipcode,
            'query': self.query,
            'products': [p.to_dict() for p in self.products],
            'success': self.success,
            'error': self.error,
            'duration_seconds': self.duration_seconds,
            'products_found': self.products_found,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
