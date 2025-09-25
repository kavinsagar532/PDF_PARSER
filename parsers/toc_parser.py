"""A module for parsing the Table of Contents (TOC) from a PDF.

This module provides the `TOCParser` class, which is responsible for
and extracting entries from the Table of Contents pages. It uses
a series of regular expressions to match different TOC formats.
"""

# Standard library imports
import re
from typing import Any, Dict, List, Optional, Tuple

# Local imports
from core.base_classes import BaseParser
from core.interfaces import TOCParserInterface
from utils.text_utils import TextProcessor


class TOCParser(BaseParser, TOCParserInterface):
    """Parses a Table of Contents with a focus on encapsulation.

    This class inherits from `BaseParser` for status tracking and
    implements the `TOCParserInterface`. Internal attributes and
    helper methods are private to ensure a clean and stable public API.
    """

    def __init__(self, doc_title: str = "USB Power Delivery Specification"):
        super().__init__("TOCParser")
        self.__doc_title = doc_title
        self.__text_processor = TextProcessor()
        self.__extraction_patterns = self.__initialize_extraction_patterns()
        self.__toc_indicators = ["table of contents", "contents"]
        self.__parsing_stats: Dict[str, Any] = {}
        self.__reset_parsing_stats()

    @property
    def doc_title(self) -> str:
        """Return the document title with this parser instance."""
        return self.__doc_title

    @doc_title.setter
    def doc_title(self, value: str) -> None:
        """Set the document title after validating it."""
        if not self.__is_valid_title(value):
            raise ValueError("Document title must be a non-empty string.")
        self.__doc_title = value

    @property
    def parsing_stats(self) -> Dict[str, Any]:
        """Return a copy of the parsing statistics."""
        return self.__parsing_stats.copy()

    def parse(
        self, input_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Implement abstract `parse` method from `ParserInterface`."""
        return self.parse_toc(input_data)

    def validate_input(self, pages: List[Dict[str, Any]]) -> bool:
        """Validate that the input is a list of page dictionaries."""
        return (
            self.__is_valid_pages_structure(pages) and
            self.__pages_have_required_fields(pages)
        )

    def parse_toc(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Orchestrate the TOC parsing process."""
        self._set_status("parsing")
        self.__reset_parsing_stats()
        try:
            if self.validation_enabled and not self.validate_input(pages):
                raise ValueError(
                    "Invalid input: pages data is not structured correctly."
                )
            
            toc_entries = self.__extract_toc_entries_from_pages(pages)
            self.__finalize_parsing()
            return toc_entries
        except Exception as e:
            self._handle_parsing_error(e, "TOC parsing")
            return []

    def __initialize_extraction_patterns(self) -> List[str]:
        """Define the regex patterns for matching TOC entries."""
        return [
            r"^\s*(?P<section_id>\d+(?:\.\d+)*)[)\.\-]?\s*(?P<title>.+?)"
            r"\s*(?:\.{2,}|\s{2,})(?P<page>\d{1,4})\s*$",
            r"^\s*(?P<section_id>\d+(?:\.\d+)*)\s+(?P<title>.+?)"
            r"\s+(?P<page>\d{1,4})\s*$",
            r"^\s*(?P<annex>Annex|Appendix)\s+(?P<section_id>[A-Z0-9]+)"
            r"[\.\s-]*\s*(?P<title>.+?)\s*(?:\.{2,}|\s{2,})"
            r"(?P<page>\d{1,4})\s*$",
            r"^(?P<title>.+?)\s*(?:\.{2,}|\s{2,})(?P<page>\d{1,4})\s*$",
        ]

    def __extract_toc_entries_from_pages(
        self, pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert pages to lines, find the TOC, and extract entries."""
        lines = self.__flatten_pages_to_lines(pages)
        start_index = self.__find_toc_start(lines)
        return self.__extract_toc_entries_from_lines(lines[start_index:])

    def __flatten_pages_to_lines(
        self, pages: List[Dict[str, Any]]
    ) -> List[Tuple[int, str]]:
        """Convert page dictionaries into a list of (page_num, line)."""
        lines = []
        for page in pages:
            page_number = self.__extract_page_number(page)
            text = page.get("text", "")
            page_lines = self.__text_processor.split_into_lines(text)
            lines.extend((page_number, line) for line in page_lines)
        return lines

    def __find_toc_start(self, lines: List[Tuple[int, str]]) -> int:
        """Find the line index where the Table of Contents begins."""
        return self.__text_processor.find_content_start(
            lines, self.__toc_indicators
        )

    def __extract_toc_entries_from_lines(
        self, lines: List[Tuple[int, str]]
    ) -> List[Dict[str, Any]]:
        """Iterate through lines and parse any that match TOC patterns."""
        toc_entries = []
        for _, line in lines:
            entry = self.__extract_single_entry(line)
            if self.__is_valid_entry(entry):
                final_entry = self.__create_toc_entry(entry)
                toc_entries.append(final_entry)
                self.__parsing_stats["entries_found"] += 1
        return toc_entries

    def __extract_single_entry(self, line_text: str) -> Dict[str, Any]:
        """Attempt to match a single line against all regex patterns."""
        clean_line = line_text.strip()
        for i, pattern in enumerate(self.__extraction_patterns):
            match = re.match(pattern, clean_line, re.IGNORECASE)
            if match:
                self.__update_pattern_usage_stats(i)
                groups = match.groupdict()
                return self.__process_match_groups(groups, clean_line)
        return {}

    def __process_match_groups(
        self, groups: Dict[str, str], original_line: str
    ) -> Dict[str, Any]:
        """Convert the captured regex groups into structured dictionary."""
        section_id = groups.get("section_id")
        if groups.get("annex"):
            section_id = self.__format_annex_id(groups, section_id)
        return {
            "section_id": section_id,
            "title": self.__clean_title(groups.get("title", "")),
            "page": self.__parse_page_number(groups.get("page")),
            "full_path": original_line,
        }

    def __create_toc_entry(
        self, entry_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assemble the final TOC entry with hierarchical data."""
        section_id = entry_data.get("section_id")
        return {
            "doc_title": self.__doc_title,
            "section_id": section_id,
            "title": entry_data.get("title"),
            "page": entry_data.get("page"),
            "level": self.__calculate_entry_level(section_id),
            "parent_id": self.__determine_parent_id(section_id),
            "full_path": entry_data.get("full_path"),
        }

    def __extract_page_number(self, page: Dict[str, Any]) -> int:
        """Safely extract the page number from a page dictionary."""
        return page.get("page", page.get("page_number", 0))

    def __is_valid_entry(self, entry: Dict[str, Any]) -> bool:
        """Check if an entry is valid by confirming it has a page."""
        return bool(entry and entry.get("page"))

    def __format_annex_id(
        self, groups: Dict[str, str], section_id: Optional[str]
    ) -> str:
        """Format a section ID for special cases like 'Annex A'."""
        annex_type = groups.get("annex", "").capitalize()
        return f"{annex_type} {section_id}".strip()

    def __clean_title(self, title: str) -> str:
        """Remove leading/trailing whitespace and periods from a title."""
        return title.strip().strip(". ")

    def __parse_page_number(self, page_str: Optional[str]) -> int:
        """Convert a page number string to an integer, defaulting to 0."""
        return int(page_str) if page_str and page_str.isdigit() else 0

    def __calculate_entry_level(self, section_id: Optional[str]) -> int:
        """Calculate the hierarchical depth of section based on its ID."""
        return len(section_id.split(".")) if section_id else 1

    def __determine_parent_id(
        self, section_id: Optional[str]
    ) -> Optional[str]:
        """Determine the parent section's ID from a given section ID."""
        if section_id and "." in section_id:
            return ".".join(section_id.split(".")[:-1])
        return None

    def __finalize_parsing(self) -> None:
        """Update the status and counters finalize the parsing process."""
        self._set_status("completed")
        self._increment_processed()

    def __reset_parsing_stats(self) -> None:
        """Reset the parsing statistics to their initial state."""
        self.__parsing_stats = {"entries_found": 0, "patterns_used": {}}

    def __update_pattern_usage_stats(self, pattern_index: int) -> None:
        """Increment the usage count for a specific regex pattern."""
        pattern_key = f"pattern_{pattern_index}"
        self.__parsing_stats["patterns_used"][pattern_key] = (
            self.__parsing_stats["patterns_used"].get(pattern_key, 0) + 1
        )

    def __is_valid_title(self, title: str) -> bool:
        """Validate that the document title is a non-empty string."""
        return isinstance(title, str) and bool(title)

    def __is_valid_pages_structure(self,pages:List[Dict[str, Any]]) -> bool:
        """Check if the input is a non-empty list."""
        return isinstance(pages, list) and bool(pages)

    def __pages_have_required_fields(
        self, pages: List[Dict[str, Any]]
    ) -> bool:
        """Check if a sample of page dictionaries contains keys."""
        sample_size = min(5, len(pages))
        return all(
            isinstance(page, dict) and
            ("page" in page or "page_number" in page) and
            "text" in page
            for page in pages[:sample_size]
        )


if __name__ == "__main__":
    print("TOCParser module is ready for use.")
