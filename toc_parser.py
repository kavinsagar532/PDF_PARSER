"""Table of Contents parsing with improved OOP design."""

# Standard library imports
import re
from typing import Dict, List, Optional, Tuple,Any

# Local imports
from base_classes import BaseParser
from interfaces import TOCParserInterface
from text_utils import TextProcessor


class TOCParser(BaseParser, TOCParserInterface):
    """Enhanced TOC parser with better encapsulation and polymorphism."""
    
    def __init__(self, doc_title: str = "Universal Serial Bus Power Delivery Specification"):
        super().__init__("TOCParser")
        self._doc_title = doc_title
        self._text_processor = TextProcessor()
        self._extraction_patterns = self._initialize_extraction_patterns()
        self._toc_indicators = ["table of contents", "contents"]
        self._parsing_stats = {"entries_found": 0, "patterns_used": {}}
    
    @property
    def doc_title(self) -> str:
        """Get document title."""
        return self._doc_title
    
    @doc_title.setter
    def doc_title(self, value: str) -> None:
        """Set document title with validation."""
        if not self._is_valid_title(value):
            raise ValueError("Document title must be a non-empty string")
        self._doc_title = value
    
    @property
    def extraction_patterns(self) -> List[str]:
        """Get list of extraction patterns."""
        return self._extraction_patterns.copy()
    
    @property
    def parsing_stats(self) -> Dict[str, Any]:
        """Get parsing statistics."""
        return self._parsing_stats.copy()
    
    def parse(self, input_data: List[Dict]) -> List[Dict]:
        """Parse method implementation for base interface."""
        return self.parse_toc(input_data)
    
    def validate_input(self, pages: List[Dict]) -> bool:
        """Validate input pages data."""
        if not self._is_valid_pages_structure(pages):
            return False
        
        return self._pages_have_required_fields(pages)
    
    def parse_toc(self, pages: List[Dict]) -> List[Dict]:
        """Parse table of contents from pages with enhanced error handling."""
        self._set_status("parsing")
        self._reset_parsing_stats()
        
        try:
            if self._should_validate() and not self.validate_input(pages):
                raise ValueError("Invalid pages data structure")
            
            toc_entries = self._extract_toc_entries_from_pages(pages)
            self._finalize_parsing(toc_entries)
            
            return toc_entries
            
        except Exception as e:
            self._handle_parsing_error(e, "TOC parsing")
            return []
    
    def _initialize_extraction_patterns(self) -> List[str]:
        """Initialize regex patterns for TOC entry extraction."""
        return [
            (r"^\s*(?P<section_id>\d+(?:\.\d+)*)[)\.\-]?\s*"
             r"(?P<title>.+?)\s*(?:\.{2,}|\s{2,})"
             r"(?P<page>\d{1,4})\s*$"),
            
            (r"^\s*(?P<section_id>\d+(?:\.\d+)*)\s+"
             r"(?P<title>.+?)\s+(?P<page>\d{1,4})\s*$"),
            
            (r"^\s*(?P<annex>Annex|Appendix)\s+(?P<section_id>[A-Z0-9]+)"
             r"[\.\s-]*\s*(?P<title>.+?)\s*(?:\.{2,}|\s{2,})"
             r"(?P<page>\d{1,4})\s*$"),
            
            (r"^(?P<title>.+?)\s*(?:\.{2,}|\s{2,})"
             r"(?P<page>\d{1,4})\s*$")
        ]
    
    def _extract_toc_entries_from_pages(self, pages: List[Dict]) -> List[Dict]:
        """Extract TOC entries from all pages."""
        lines = self._flatten_pages_to_lines(pages)
        start_index = self._find_toc_start(lines)
        return self._extract_toc_entries_from_lines(lines[start_index:])
    
    def _flatten_pages_to_lines(self, pages: List[Dict]) -> List[Tuple[int, str]]:
        """Convert pages into a list of (page_number, line_text) tuples."""
        lines = []
        
        for page in pages:
            page_number = self._extract_page_number(page)
            text = page.get("text", "") or ""
            
            page_lines = self._text_processor.split_into_lines(text)
            lines.extend((page_number, line) for line in page_lines)
        
        return lines
    
    def _find_toc_start(self, lines: List[Tuple[int, str]]) -> int:
        """Find the starting index of TOC content."""
        return self._text_processor.find_content_start(lines, self._toc_indicators)
    
    def _extract_toc_entries_from_lines(self, lines: List[Tuple[int, str]]) -> List[Dict]:
        """Extract TOC entries from processed lines."""
        toc_entries = []
        
        for page_num, line in lines:
            entry = self._extract_single_entry(line)
            
            if self._is_valid_entry(entry):
                final_entry = self._create_toc_entry(entry)
                toc_entries.append(final_entry)
                self._parsing_stats["entries_found"] += 1
        
        return toc_entries
    
    def _extract_single_entry(self, line_text: str) -> Dict:
        """Extract section info from a single line using patterns."""
        clean_line = line_text.strip()
        
        for i, pattern in enumerate(self._extraction_patterns):
            match = re.match(pattern, clean_line, re.IGNORECASE)
            
            if match:
                self._update_pattern_usage_stats(i)
                groups = match.groupdict()
                return self._process_match_groups(groups, clean_line)
        
        return {}
    
    def _process_match_groups(self, groups: Dict, 
                             original_line: str) -> Dict:
        """Process regex match groups into structured data."""
        section_id = groups.get("section_id")
        
        if groups.get("annex"):
            section_id = self._format_annex_id(groups, section_id)
        
        return {
            "section_id": section_id,
            "title": self._clean_title(groups.get("title", "")),
            "page": self._parse_page_number(groups.get("page")),
            "full_path": original_line
        }
    
    def _create_toc_entry(self, entry_data: Dict) -> Dict:
        """Create final TOC entry with hierarchical information."""
        section_id = entry_data.get("section_id")
        level = self._calculate_entry_level(section_id)
        parent_id = self._determine_parent_id(section_id)
        
        return {
            "doc_title": self._doc_title,
            "section_id": section_id,
            "title": entry_data.get("title"),
            "page": entry_data.get("page"),
            "level": level,
            "parent_id": parent_id,
            "full_path": entry_data.get("full_path")
        }
    
    def _extract_page_number(self, page: Dict) -> int:
        """Extract page number from page dictionary."""
        return page.get("page") or page.get("page_number") or 0
    
    def _is_valid_entry(self, entry: Dict) -> bool:
        """Check if extracted entry is valid."""
        return entry and entry.get("page")
    
    def _format_annex_id(self, groups: Dict, section_id: str) -> str:
        """Format section ID for annex entries."""
        annex_type = groups["annex"].capitalize()
        return f"{annex_type} {section_id}"
    
    def _clean_title(self, title: str) -> str:
        """Clean and format entry title."""
        return title.strip().strip(". ")
    
    def _parse_page_number(self, page_str: str) -> int:
        """Parse page number from string."""
        return int(page_str) if page_str else 0
    
    def _calculate_entry_level(self, section_id: str) -> int:
        """Calculate hierarchical level of entry."""
        return len(section_id.split(".")) if section_id else 1
    
    def _determine_parent_id(self, section_id: str) -> Optional[str]:
        """Determine parent ID for hierarchical entries."""
        if section_id and "." in section_id:
            return ".".join(section_id.split(".")[:-1])
        return None
    
    def _finalize_parsing(self, toc_entries: List[Dict]) -> None:
        """Finalize parsing process and update status."""
        self._set_status("completed")
        self._increment_processed()
    
    def _reset_parsing_stats(self) -> None:
        """Reset parsing statistics."""
        self._parsing_stats = {"entries_found": 0, "patterns_used": {}}
    
    def _update_pattern_usage_stats(self, pattern_index: int) -> None:
        """Update statistics for pattern usage."""
        pattern_key = f"pattern_{pattern_index}"
        current_count = self._parsing_stats["patterns_used"].get(pattern_key, 0)
        self._parsing_stats["patterns_used"][pattern_key] = current_count + 1
    
    def _is_valid_title(self, title: str) -> bool:
        """Validate document title."""
        return title and isinstance(title, str)
    
    def _is_valid_pages_structure(self, pages: List[Dict]) -> bool:
        """Check if pages have valid structure."""
        return pages and isinstance(pages, list)
    
    def _pages_have_required_fields(self, pages: List[Dict]) -> bool:
        """Check if pages have required fields."""
        sample_size = min(5, len(pages))
        sample_pages = pages[:sample_size]
        
        return all(
            isinstance(page, dict) and 
            ("page" in page or "page_number" in page) and 
            "text" in page
            for page in sample_pages
        )
    
    def _should_validate(self) -> bool:
        """Check if input validation should be performed."""
        return self.validation_enabled


if __name__ == "__main__":
    print("TOCParser module ready")
