"""A module for calculating various coverage metrics for the parsed data.

This module provides `CoverageCalculator` class, a component specialized
in calculating like page coverage, TOC coverage, and section coverage.
"""

# Standard library imports
from typing import Any, Dict, List, Set


class CoverageCalculator:
    """Calculates various coverage metrics with a focus on encapsulation.

    provides a suite of methods for calculating different coverage
    percentages. All internal state helper methods are private to ensure a
    clean and stable public API.
    """

    def __init__(self):
        self.__calculations_performed = 0

    @property
    def calculations_performed(self) -> int:
        """Return total number of calculations made by this instance."""
        return self.__calculations_performed

    def calculate_page_coverage(
        self, pages_with_text: int, total_pages: int
    ) -> float:
        """Calculate the percentage of pages that contain text."""
        self.__calculations_performed += 1
        return self.__safe_percentage_calculation(pages_with_text, total_pages)

    def calculate_toc_coverage(
        self, covered_pages: int, total_pages: int
    ) -> float:
        """Calculate the percentage of pages covered by the TOC."""
        self.__calculations_performed += 1
        return self.__safe_percentage_calculation(covered_pages, total_pages)

    def calculate_section_coverage(
        self, sections_count: int, pages_with_text: int
    ) -> float:
        """Calculate the ratio of parsed sections to pages with text."""
        self.__calculations_performed += 1
        return self.__safe_percentage_calculation(
            sections_count, pages_with_text
        )

    def calculate_toc_pages_covered(
        self, toc_entries: List[Dict[str, Any]], total_pages: int
    ) -> int:
        """Calculate the total number of unique pages covered by TOCs."""
        valid_entries = self.__filter_valid_toc_entries(toc_entries)
        covered_pages = self.__calculate_covered_page_set(
            valid_entries, total_pages
        )
        self.__calculations_performed += 1
        return len(covered_pages)

    def __safe_percentage_calculation(
        self, numerator: int, denominator: int
    ) -> float:
        """Calculate a percentage safely, handling division by zero."""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator * 100), 2)

    def __filter_valid_toc_entries(
        self, toc_entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter and sort TOC entries with valid page numbers."""
        valid_entries = [
            entry for entry in toc_entries
            if isinstance(entry.get("page"), int) and entry["page"] > 0
        ]
        return sorted(valid_entries, key=lambda x: x.get("page", 0))

    def __calculate_covered_page_set(
        self, entries: List[Dict[str, Any]], total_pages: int
    ) -> Set[int]:
        """Calculate the set of page numbers covered by TOC entries."""
        covered_pages: Set[int] = set()
        for i, entry in enumerate(entries):
            page_range = self.__get_entry_page_range(
                entry, entries, i, total_pages
            )
            covered_pages.update(page_range)
        return covered_pages

    def __get_entry_page_range(
        self, entry: Dict[str, Any], all_entries: List[Dict[str, Any]],
        current_index: int, total_pages: int
    ) -> range:
        """Determine the page range for a single TOC entry."""
        start = int(entry.get("page", 0))
        
        if current_index + 1 < len(all_entries):
            end = int(all_entries[current_index + 1].get("page", 0)) - 1
        else:
            end = total_pages
        
        return range(start, max(end, start) + 1)
