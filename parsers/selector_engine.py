#!/usr/bin/env python3
"""Selector engine for parsing HTML with multiple fallback selectors."""
from typing import List, Optional, Dict
from bs4 import BeautifulSoup


class SelectorEngine:
    """
    Flexible selector engine supporting CSS selectors with fallbacks.

    Features:
    - Multiple selector fallbacks
    - Attribute extraction
    - Text normalization
    """

    def __init__(self, html: str):
        """
        Initialize selector engine with HTML content.

        Args:
            html: HTML content to parse
        """
        self.soup = BeautifulSoup(html, 'lxml')

    def select_one(
        self,
        selectors: List[str],
        attr: Optional[str] = None
    ) -> Optional[str]:
        """
        Try multiple selectors and return first match.

        Args:
            selectors: List of CSS selectors to try
            attr: Optional attribute to extract (e.g., 'href', 'src')

        Returns:
            Extracted text or attribute value, or None if no match found
        """
        for selector in selectors:
            try:
                element = self.soup.select_one(selector)
                if element:
                    if attr:
                        # Extract attribute
                        value = element.get(attr)
                        if value:
                            return str(value).strip()
                    else:
                        # Extract text content
                        text = element.get_text(strip=True)
                        if text:
                            return text
            except Exception:
                continue

        return None

    def select_many(
        self,
        selectors: List[str],
        attr: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Select multiple elements and return list of values.

        Args:
            selectors: List of CSS selectors to try
            attr: Optional attribute to extract
            limit: Maximum number of results to return

        Returns:
            List of extracted values
        """
        results = []

        for selector in selectors:
            try:
                elements = self.soup.select(selector)
                if elements:
                    for element in elements:
                        if limit and len(results) >= limit:
                            return results

                        if attr:
                            value = element.get(attr)
                            if value:
                                results.append(str(value).strip())
                        else:
                            text = element.get_text(strip=True)
                            if text:
                                results.append(text)

                    if results:
                        # Found results with this selector, stop trying others
                        break
            except Exception:
                continue

        return results

    def extract_table(self, selectors: List[str]) -> Dict[str, str]:
        """
        Extract key-value pairs from a table (e.g., product specifications).

        Args:
            selectors: List of CSS selectors for table elements

        Returns:
            Dictionary of key-value pairs
        """
        specs = {}

        for selector in selectors:
            try:
                table = self.soup.select_one(selector)
                if not table:
                    continue

                # Try to find rows
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            specs[key] = value

                # If we found any specs, return them
                if specs:
                    break

            except Exception:
                continue

        return specs

    def has_text(self, text: str, case_sensitive: bool = False) -> bool:
        """
        Check if HTML contains specific text.

        Args:
            text: Text to search for
            case_sensitive: Whether search is case sensitive

        Returns:
            True if text is found, False otherwise
        """
        page_text = self.soup.get_text()

        if not case_sensitive:
            return text.lower() in page_text.lower()

        return text in page_text

    def __str__(self) -> str:
        """String representation."""
        return f"SelectorEngine(html_length={len(str(self.soup))})"
