"""A module for processing Table of Contents (TOC) data.

This module provides the `TOCProcessor` class, which is responsible for
validating TOC entries and calculating the page coverage of those entries.
It serves as a helper component within the section parsing workflow.
"""

# Standard library imports
from typing import Any, Dict, List, Set


class TOCProcessor:
    """Processes and analyzes a list of Table of Contents entries.

    This class provides functionality to filter for valid TOC entries to
    determine the set of pages covered. All internal state and helper
    methods are private to ensure a clean public API.
    """

    def __init__(self):
        self.__processed_entries = 0

    @property
    def processed_entries(self) -> int:
        """Return the total number of TOC entries processed."""
        return self.__processed_entries

    def validate_toc_entries(
        self, toc_entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter valid TOC entries and sort them by page."""
        valid_entries = [
            entry for entry in toc_entries if self.__is_valid_entry(entry)
        ]
        return sorted(valid_entries, key=lambda x: x.get("page", 0))

    def calculate_page_coverage(
        self, toc_entries: List[Dict[str, Any]], total_pages: int
    ) -> Set[int]:
        """Calculate the set of page numbers covered by TOC entries."""
        covered_pages: Set[int] = set()
        # Ensure entries are sorted by page number before calculating .
        sorted_entries = self.validate_toc_entries(toc_entries)

        for i, entry in enumerate(sorted_entries):
            page_range = self.__calculate_entry_page_range(
                entry, sorted_entries, i, total_pages
            )
            covered_pages.update(page_range)
            self.__processed_entries += 1
        
        return covered_pages

    def __is_valid_entry(self, entry: Dict[str, Any]) -> bool:
        """Check if a TOC entry has a positive integer page number."""
        page = entry.get("page")
        return isinstance(page, int) and page > 0

    def __calculate_entry_page_range(
        self, entry: Dict[str, Any], all_entries: List[Dict[str, Any]],
        current_index: int, total_pages: int
    ) -> range:
        """Calculate the page range for a single TOC entry."""
        start_page = int(entry["page"])
        
        # Determine the end page by looking at the start of the next entry.
        if current_index + 1 < len(all_entries):
            end_page = int(all_entries[current_index + 1]["page"]) - 1
        else:
            # If it's the last entry, it covers all pages to the end.
            end_page = total_pages
        
        # Ensure the end page is not before the start page.
        end_page = max(end_page, start_page)
        return range(start_page, end_page + 1)
