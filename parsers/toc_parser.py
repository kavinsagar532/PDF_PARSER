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
        """Define precise, high-quality regex patterns for matching TOC
        entries."""
        return [
            # Standard numbered sections (1.1, 2.3.4, etc.) with dots
            # leading to page
            r"^\s*(?P<section_id>\d+(?:\.\d+)*)\s+(?P<title>[^.]+?)"
            r"\s*\.{3,}\s*(?P<page>\d{1,4})\s*$",
            
            # Numbered sections with clear title and page separation
            r"^\s*(?P<section_id>\d+(?:\.\d+)*)\s+(?P<title>.{5,80}?)"
            r"\s{3,}(?P<page>\d{1,4})\s*$",
            
            # Table/Figure references (Table 1.1, Figure 2.3, etc.)
            r"^\s*(?P<prefix>Table|Figure)\s*(?P<section_id>\d+(?:\.\d+)*)"
            r"\s+(?P<title>.{5,100}?)\s*\.{3,}\s*(?P<page>\d{1,4})\s*$",
            
            # Appendix/Annex sections (Appendix A, Annex B, etc.)
            r"^\s*(?P<annex>Appendix|Annex)\s+(?P<section_id>[A-Z])"
            r"\s+(?P<title>.{5,80}?)\s*\.{3,}\s*(?P<page>\d{1,4})\s*$",
            
            # Chapter sections
            r"^\s*(?P<chapter>Chapter)\s+(?P<section_id>\d+)"
            r"\s+(?P<title>.{5,80}?)\s*\.{3,}\s*(?P<page>\d{1,4})\s*$",
            
            # Simple title with dots and page (high confidence pattern)
            r"^(?P<title>[A-Z][^.]{10,80}?)\s*\.{4,}\s*(?P<page>\d{1,4})\s*$",
            
            # Alphabetic sections (A.1, B.2, etc.)
            r"^\s*(?P<section_id>[A-Z]\.\d+(?:\.\d+)*)\s+(?P<title>.{5,80}?)"
            r"\s*\.{3,}\s*(?P<page>\d{1,4})\s*$",
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
        """Iterate through lines and parse any that match TOC patterns
        with enhanced detection."""
        toc_entries = []
        potential_entries = []
        
        for page_num, line in lines:
            # Primary extraction using high-quality regex patterns
            entry = self.__extract_single_entry(line)
            if (self.__is_valid_entry(entry) and 
                    self.__is_high_quality_entry(entry)):
                final_entry = self.__create_toc_entry(entry)
                toc_entries.append(final_entry)
                self.__parsing_stats["entries_found"] += 1
            else:
                # Collect potential entries for fallback processing
                potential_entry = self.__analyze_potential_toc_line(
                    line, page_num
                )
                if potential_entry:
                    potential_entries.append(potential_entry)
        
        # Apply enhanced pattern matching for missed genuine entries
        enhanced_entries = self.__apply_enhanced_pattern_matching(
            toc_entries, lines
        )
        toc_entries.extend(enhanced_entries)
        
        # Apply fallback extraction for missed genuine entries
        fallback_entries = self.__apply_fallback_extraction(potential_entries)
        toc_entries.extend(fallback_entries)
        
        # Sort entries by page number and remove duplicates
        toc_entries = self.__validate_and_clean_entries(toc_entries)
        
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
        """Convert the captured regex groups into structured dictionary
        with enhanced processing."""
        section_id = groups.get("section_id")
        
        # Handle special section types
        if groups.get("annex"):
            section_id = self.__format_annex_id(groups, section_id)
        elif groups.get("chapter"):
            section_id = f"Chapter {section_id}" if section_id else None
        
        return {
            "section_id": section_id,
            "title": self.__clean_title(groups.get("title", "")),
            "page": self.__parse_page_number(groups.get("page")),
            "full_path": original_line
        }

    def __create_toc_entry(
        self, entry_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assemble the final TOC entry with hierarchical data and
        enhanced metadata."""
        section_id = entry_data.get("section_id")
        return {
            "doc_title": self.__doc_title,
            "section_id": section_id,
            "title": entry_data.get("title"),
            "page": entry_data.get("page"),
            "level": self.__calculate_entry_level(section_id),
            "parent_id": self.__determine_parent_id(section_id),
            "full_path": entry_data.get("full_path"),
            "tags": self.__generate_entry_tags(entry_data)
        }

    def __extract_page_number(self, page: Dict[str, Any]) -> int:
        """Safely extract the page number from a page dictionary."""
        return page.get("page", page.get("page_number", 0))

    def __is_valid_entry(self, entry: Dict[str, Any]) -> bool:
        """Check if an entry is valid by confirming it has a page."""
        return bool(entry and entry.get("page"))
    
    def __is_high_quality_entry(self, entry: Dict[str, Any]) -> bool:
        """Check if an entry meets high quality standards."""
        title = entry.get("title", "")
        page = entry.get("page", 0)
        
        # Title quality checks
        if not title or len(title.strip()) < 5:
            return False
        
        # Reject overly long titles (likely parsing errors)
        if len(title) > 120:
            return False
        
        # Page number validation
        if not isinstance(page, int) or page < 1 or page > 1047:
            return False
        
        # Reject entries that look like parsing artifacts
        if title.count('.') > 15:  # Too many dots
            return False
            
        # Reject technical data fragments
        if self.__looks_like_technical_data(title):
            return False
            
        # Reject entries with too many numbers (likely data tables)
        numbers = sum(1 for char in title if char.isdigit())
        if numbers > len(title) * 0.4:  # More than 40% numbers
            return False
            
        return True
    
    def __looks_like_technical_data(self, title: str) -> bool:
        """Check if title looks like technical data rather than a TOC entry."""
        title_lower = title.lower().strip()
        
        # Common technical data patterns
        technical_patterns = [
            r'^\d+\s+\d+\s+\d+',  # Multiple numbers in sequence
            r'^[01\s]+$',  # Binary data
            r'hex\s+data',  # Hex data references
            r'bit\s*=\s*\d',  # Bit assignments
            r'k-code',  # K-code references
            r'byte\s+\d',  # Byte references
            r'^[a-z]\d+rx',  # Signal names like Y3Rx
            r'preamble.*training',  # Technical preamble
            r'data\s+object\s+\d',  # Data object references
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, title_lower):
                return True
                
        # Check for very short technical fragments
        if len(title.strip()) < 10 and any(char.isdigit() for char in title):
            return True
            
        return False

    def __format_annex_id(
        self, groups: Dict[str, str], section_id: Optional[str]
    ) -> str:
        """Format a section ID for special cases like 'Annex A'."""
        annex_type = groups.get("annex", "").capitalize()
        return f"{annex_type} {section_id}".strip()

    def __clean_title(self, title: str) -> str:
        """Clean and validate title to prevent malformed entries."""
        if not title:
            return ""
        
        # Remove leading/trailing whitespace
        cleaned = title.strip()
        
        # Remove excessive dots (more than 3 consecutive)
        cleaned = re.sub(r'\.{4,}', '', cleaned)
        
        # Prevent overly long concatenated titles (likely parsing errors)
        if len(cleaned) > 120:
            # Find a reasonable break point at sentence or clause boundary
            sentences = cleaned.split('.')
            if len(sentences) > 1 and len(sentences[0]) < 80:
                cleaned = sentences[0].strip()
            else:
                # Break at first reasonable point
                cleaned = cleaned[:80].strip()
        
        # Remove trailing dots and spaces, but preserve meaningful punctuation
        while cleaned and cleaned[-1] in '. ':
            cleaned = cleaned[:-1]
        
        # Remove excessive whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Handle common formatting issues
        cleaned = cleaned.replace('  ', ' ')  # Double spaces
        cleaned = cleaned.replace(' .', '.')   # Space before period
        
        return cleaned

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
    
    def __generate_entry_tags(self, entry_data: Dict[str, Any]) -> List[str]:
        """Generate tags for TOC entries based on content analysis."""
        tags = []
        title = entry_data.get("title", "").lower()
        
        # Content type tags
        intro_words = ['introduction', 'overview', 'summary']
        if any(word in title for word in intro_words):
            tags.append('introductory')
        concl_words = ['conclusion', 'summary', 'results']
        if any(word in title for word in concl_words):
            tags.append('concluding')
        supp_words = ['appendix', 'annex', 'supplement']
        if any(word in title for word in supp_words):
            tags.append('supplementary')
        ref_words = ['reference', 'bibliography', 'citation']
        if any(word in title for word in ref_words):
            tags.append('reference')
        visual_words = ['table', 'figure', 'diagram', 'chart']
        if any(word in title for word in visual_words):
            tags.append('visual_content')
        spec_words = ['specification', 'requirement', 'standard']
        if any(word in title for word in spec_words):
            tags.append('specification')
        
        # Remove extraction method tag - no longer needed
        
        return tags

    def __apply_enhanced_pattern_matching(
        self, original_entries: List[Dict[str, Any]],
        lines: List[Tuple[int, str]]
    ) -> List[Dict[str, Any]]:
        """Apply enhanced pattern matching for missed genuine TOC
        entries."""
        enhanced_entries = []
        
        # Enhanced patterns for genuine TOC entries that might be
        # missed
        enhanced_patterns = [
            # More flexible numbered sections
            r"^\s*(?P<section_id>\d+(?:\.\d+)*)\s*(?P<title>.{3,100}?)"
            r"\s+(?P<page>\d{1,4})\s*$",
            
            # Table and Figure entries with more flexibility
            r"^\s*(?P<prefix>Table|Figure|Equation)\s*"
            r"(?P<section_id>\d+(?:\.\d+)*)\s*(?P<title>.{3,80}?)"
            r"\s+(?P<page>\d{1,4})\s*$",
            
            # List items and bullet points
            r"^\s*[•\-\*]\s*(?P<title>.{5,80}?)\s+(?P<page>\d{1,4})\s*$",
            
            # Subsection patterns
            r"^\s*(?P<section_id>\d+\.\d+\.\d+)\s+(?P<title>.{5,60}?)"
            r"\s+(?P<page>\d{1,4})\s*$",
            
            # Reference and bibliography entries
            r"^\s*(?P<title>References?|Bibliography|Index|Glossary)"
            r"\s+(?P<page>\d{1,4})\s*$",
            
            # Roman numeral sections
            r"^\s*(?P<section_id>[IVX]+(?:\.[IVX]+)*)\s+(?P<title>.{5,80}?)"
            r"\s*\.{3,}\s*(?P<page>\d{1,4})\s*$",
            
            # Lettered sections (A, B, C, etc.)
            r"^\s*(?P<section_id>[A-Z](?:\.[A-Z])*(?:\.\d+)*)"
            r"\s+(?P<title>.{5,80}?)\s*\.{3,}\s*(?P<page>\d{1,4})\s*$",
        ]
        
        existing_pages = {entry.get('page') for entry in original_entries}
        existing_titles = {
            entry.get('title', '').lower() for entry in original_entries
        }
        
        for page_num, line in lines:
            clean_line = line.strip()
            
            # Skip if we already have an entry for this line's content
            if any(clean_line in entry.get('full_path', '')
                   for entry in original_entries):
                continue
                
            for pattern in enhanced_patterns:
                match = re.match(pattern, clean_line, re.IGNORECASE)
                if match:
                    groups = match.groupdict()
                    page = self.__parse_page_number(groups.get("page"))
                    title = self.__clean_title(groups.get("title", ""))
                    
                    # Quality checks for enhanced entries - must be genuine
                    # TOC content
                    if (page and 1 <= page <= 1047 and 
                        len(title.strip()) >= 5 and
                        title.lower() not in existing_titles and
                        not title.lower().startswith('page ') and
                        not self.__looks_like_technical_data(title) and
                        self.__looks_like_genuine_toc_entry(title)):
                        
                        enhanced_entry = {
                            "doc_title": self.__doc_title,
                            "section_id": groups.get(
                                "section_id", f"Section-{page}"
                            ),
                            "title": title,
                            "page": page,
                            "level": self.__calculate_entry_level(
                                groups.get("section_id")
                            ),
                            "parent_id": self.__determine_parent_id(
                                groups.get("section_id")
                            ),
                            "full_path": clean_line,
                            "tags": ["enhanced_extraction"]
                        }
                        
                        enhanced_entries.append(enhanced_entry)
                        existing_pages.add(page)
                        existing_titles.add(title.lower())
                        break
        
        return enhanced_entries
    
    def __looks_like_genuine_toc_entry(self, title: str) -> bool:
        """Check if title looks like a genuine TOC entry."""
        title_clean = title.strip()
        
        # Must have reasonable length
        if len(title_clean) < 5 or len(title_clean) > 100:
            return False
            
        # Should contain meaningful words
        words = title_clean.split()
        if len(words) < 2:
            return False
            
        # Check for TOC-like keywords
        toc_keywords = [
            'introduction', 'overview', 'specification', 'requirements',
            'protocol', 'interface', 'power', 'delivery', 'usb',
            'connector', 'cable', 'message', 'communication',
            'appendix', 'annex', 'reference', 'glossary', 'index',
            'chapter', 'section', 'figure', 'table', 'example'
        ]
        
        title_lower = title_clean.lower()
        has_toc_keyword = any(
            keyword in title_lower for keyword in toc_keywords
        )
        
        # Should either have TOC keywords or look like a proper heading
        if has_toc_keyword:
            return True
            
        # Check if it looks like a proper heading (starts with capital,
        # reasonable structure)
        if (title_clean[0].isupper() and
                not title_clean.isupper() and  # Not all caps
                len([w for w in words if len(w) > 2]) >= 2):
            # At least 2 substantial words
            return True
            
        return False

    def __finalize_parsing(self) -> None:
        """Update the status and counters finalize the parsing process."""
        self._set_status("completed")
        self._increment_processed()
        
        # Store parsing statistics (removed verbose output)
        stats = self.__parsing_stats

    def __reset_parsing_stats(self) -> None:
        """Reset the parsing statistics to their initial state."""
        self.__parsing_stats = {
            "entries_found": 0, 
            "patterns_used": {},
            "fallback_entries": 0,
            "duplicates_removed": 0,
            "invalid_entries_filtered": 0
        }

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
    
    def __analyze_potential_toc_line(
        self, line: str, page_num: int
    ) -> Optional[Dict[str, Any]]:
        """Analyze lines that didn't match regex patterns for potential
        TOC content."""
        clean_line = line.strip()
        if len(clean_line) < 5 or len(clean_line) > 200:
            return None
        
        # Look for page numbers at the end
        words = clean_line.split()
        if len(words) < 2:
            return None
        
        # Check if last word could be a page number
        last_word = words[-1]
        if last_word.isdigit() and 1 <= int(last_word) <= 9999:
            title_part = ' '.join(words[:-1]).strip()
            if title_part and not title_part.isdigit():
                return {
                    'line': clean_line,
                    'potential_title': title_part,
                    'potential_page': int(last_word),
                    'source_page': page_num,
                    'confidence': self.__calculate_toc_confidence(clean_line)
                }
        
        return None
    
    def __calculate_toc_confidence(self, line: str) -> float:
        """Calculate confidence score for potential TOC entries."""
        score = 0.0
        
        # Check for common TOC indicators
        toc_keywords = [
            'introduction', 'overview', 'summary', 'conclusion',
            'references', 'appendix', 'index', 'glossary', 'abstract'
        ]
        
        line_lower = line.lower()
        for keyword in toc_keywords:
            if keyword in line_lower:
                score += 0.3
                break
        
        # Check for dots or spaces (typical TOC formatting)
        if '..' in line or '  ' in line:
            score += 0.2
        
        # Check for reasonable title length
        words = line.split()
        if 2 <= len(words) <= 15:
            score += 0.2
        
        # Check for capitalization patterns
        if any(word[0].isupper() for word in words if word):
            score += 0.1
        
        return min(1.0, score)
    
    def __apply_fallback_extraction(
        self, potential_entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply fallback methods to extract missed TOC entries."""
        fallback_entries = []
        
        # Filter by higher confidence threshold and quality
        high_confidence_entries = [
            entry for entry in potential_entries 
            if (entry.get('confidence', 0) >= 0.6 and  # Higher threshold
                not self.__looks_like_technical_data(
                    entry.get('potential_title', '')
                ) and
                self.__looks_like_genuine_toc_entry(
                    entry.get('potential_title', '')
                ))
        ]
        
        for entry in high_confidence_entries:
            title = entry['potential_title']
            
            # Additional quality check for fallback entries
            if (len(title.strip()) >= 8 and  # longer minimum
                len(title.split()) >= 2 and  # At least 2 words
                not title.lower().startswith(
                    ('error', 'data object', 'byte', 'bit')
                )):
                
                fallback_entry = {
                    'section_id': None,  # No section ID for fallback entries
                    'title': title,
                    'page': entry['potential_page'],
                    'full_path': entry['line']
                }
                
                final_entry = self.__create_toc_entry(fallback_entry)
                fallback_entries.append(final_entry)
                self.__parsing_stats["entries_found"] += 1
        
        return fallback_entries
    
    def __validate_and_clean_entries(
        self, entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and clean the extracted TOC entries."""
        if not entries:
            return entries
        # Remove duplicates based on page number and title similarity
        unique_entries = []
        seen_combinations = set()
        
        for entry in sorted(
            entries, key=lambda x: (x.get('page', 0), x.get('title', ''))
        ):
            page = entry.get('page', 0)
            title = entry.get('title', '').lower().strip()
            
            # Create a key for duplicate detection
            key = (page, title[:50])  # Use first 50 chars of title
            
            if key not in seen_combinations:
                seen_combinations.add(key)
                unique_entries.append(entry)
        
        # Validate page number sequence
        validated_entries = []
        for entry in unique_entries:
            page = entry.get('page', 0)
            if 1 <= page <= 9999:  # Reasonable page range
                validated_entries.append(entry)
        
        return validated_entries


if __name__ == "__main__":
    print("TOCParser module is ready for use.")
