"""A module for managing and accessing PDF page content efficiently.

This module provides the `PageManager` class, which is designed to hold all
page data from a PDF and provide quick, dictionary-based access to the text
content of any page or range of pages.
"""

# Standard library imports
from typing import Any, Dict, List


class PageManager:
    """Manages access to page data with a focus on performance.

    This class pre-processes a list of page data into a dictionary for
    fast lookups. All internal data structures and helper methods are
    private to ensure a clean and stable public API.
    """

    def __init__(self, pages_data: List[Dict[str, Any]]):
        self.__pages_by_number = self.__organize_pages(pages_data)
        self.__total_pages = len(pages_data)

    @property
    def total_pages(self) -> int:
        """Return the total number of pages managed by this instance."""
        return self.__total_pages

    def get_page_content(self, page_number: int) -> str:
        """Return the text content of a single page, or an empty string."""
        return self.__pages_by_number.get(page_number, "")

    def get_content_range(self, start_page: int, end_page: int) -> str:
        """Return the combined text content of a range of pages."""
        # Ensure the page range is valid.
        start = max(1, start_page)
        end = min(self.total_pages, end_page)

        content_parts = [
            self.get_page_content(page_num)
            for page_num in range(start, end + 1)
        ]
        return "\n".join(content_parts).strip()

    def __organize_pages(
        self, pages_data: List[Dict[str, Any]]
    ) -> Dict[int, str]:
        """Convert a list of dictionaries into page_number -> text map."""
        return {
            page.get("page", 0): page.get("text", "")
            for page in pages_data
        }
