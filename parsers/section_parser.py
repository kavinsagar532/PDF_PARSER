"""A module for parsing the main sections of a document.

This module provides the `SectionParser` class, as an orchestrator
for the entire section parsing workflow. It coordinates a variety of helper
components to identify, extract, and structure the document's content.
"""

# Standard library imports
import os
import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Set, Tuple

# Local imports
from core.base_classes import BaseParser
from parsers.heading_strategies import HeadingDetector
from utils.helpers import JSONLHandler
from core.interfaces import SectionParserInterface
from parsers.section.section_data import Section
from parsers.section.page_manager import PageManager
from parsers.section.toc_processor import TOCProcessor
from parsers.section.section_builder import SectionBuilder


class SectionParser(BaseParser, SectionParserInterface):
    """parsing of document sections using a component-based
    design.

    This class composes multiple helper objects, each with a distinct
    responsibility,parse sections from a document. All internal state and
    helper methods are private to maintain a clean public API.
    """

    def __init__(
        self, pdf_path: str, toc_file: str = "usb_pd_toc.jsonl",
        pages_file: str = "usb_pd_pages.jsonl",
        doc_title: str = "USB Power Delivery Specification"
    ):
        super().__init__("SectionParser")
        self.__pdf_path = pdf_path
        self.__toc_file = toc_file
        self.__pages_file = pages_file
        self.__doc_title = doc_title
        
        # Composition of helper components with enhanced capabilities
        self.__file_handler = JSONLHandler()
        self.__heading_detector = HeadingDetector()
        self.__toc_processor = TOCProcessor()
        self.__section_builder = SectionBuilder(doc_title)

    def parse(
        self, input_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """The abstract `parse` method from `ParserInterface`."""
        return self.parse_sections(toc_entries=input_data)

    def validate_input(
        self, toc_entries: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """TOC entries are provided or required files exist."""
        if toc_entries is None:
            return self.__validate_required_files()
        return isinstance(toc_entries, list)

    def parse_sections(
        self, toc_entries: Optional[List[Dict[str, Any]]] = None,
        output_file: str = "usb_pd_spec.jsonl"
    ) -> List[Dict[str, Any]]:
        """Orchestrate the full section parsing workflow."""
        self._set_status("parsing")
        try:
            if self.validation_enabled and not self.validate_input(
                toc_entries
            ):
                raise ValueError(
                    "Input validation failed: Missing TOC data or files."
                )

            pages_data, toc_data = self.__load_input_data(toc_entries)
            all_sections = self.__process_all_sections(pages_data, toc_data)
            self.__save_sections(all_sections, output_file)
            self.__finalize_parsing(all_sections)
            
            return [asdict(section) for section in all_sections]
        except Exception as e:
            self._handle_parsing_error(e, "section parsing")
            return []

    def __validate_required_files(self) -> bool:
        """Check if the necessary TOC and pages files exist on disk."""
        return (os.path.exists(self.__toc_file) and
                os.path.exists(self.__pages_file))

    def __load_input_data(
        self, toc_entries: Optional[List[Dict[str, Any]]]
    ) -> Tuple[List, List]:
        """Load page and TOC data from files or provided TOC entries."""
        pages_data = list(
            self.__file_handler.read_jsonl(self.__pages_file)
        )
        toc_data = (
            toc_entries if toc_entries is not None
            else list(
                self.__file_handler.read_jsonl(self.__toc_file)
            )
        )
        return pages_data, toc_data

    def __process_all_sections(
        self, pages_data: List[Dict[str, Any]],
        toc_data: List[Dict[str, Any]]
    ) -> List[Section]:
        """Coordinate the processing of TOC-based and non-TOC pages with
        comprehensive enhancement."""
        page_manager = PageManager(pages_data)
        valid_toc = self.__toc_processor.validate_toc_entries(toc_data)
        
        toc_sections = self.__process_toc_sections(valid_toc, page_manager)
        
        covered_pages = self.__toc_processor.calculate_page_coverage(
            valid_toc, page_manager.total_pages
        )
        page_sections = self.__process_uncovered_pages(
            covered_pages, page_manager
        )
        
        # Apply intelligent content-based section extraction
        content_sections = self.__extract_content_based_sections(
            pages_data, page_manager, toc_sections + page_sections
        )
        
        return toc_sections + page_sections + content_sections

    def __process_toc_sections(
        self, toc_entries: List[Dict[str, Any]],
        page_manager: PageManager
    ) -> List[Section]:
        """Build `Section` objects for each entry in the TOC."""
        sections = []
        for i, entry in enumerate(toc_entries):
            try:
                content = self.__extract_section_content(
                    entry, toc_entries, i, page_manager
                )
                section = self.__section_builder.build_from_toc_entry(
                    entry, content
                )
                sections.append(section)
            except Exception as e:
                print(f"Error processing TOC entry {i}: {e}")
                print(f"Entry: {entry}")
                # Continue with next entry instead of failing
                continue
        return sections

    def __extract_section_content(
        self, entry: Dict[str, Any],
        all_entries: List[Dict[str, Any]],
        current_index: int, page_manager: PageManager
    ) -> str:
        """Extract comprehensive content for a TOC entry including text,
        tables, and images."""
        start_page = int(entry["page"])
        end_page = page_manager.total_pages
        if current_index + 1 < len(all_entries):
            end_page = int(all_entries[current_index + 1]["page"]) - 1
        
        # Get comprehensive content from the enhanced page manager
        content = page_manager.get_comprehensive_content_range(
            start_page, end_page
        )
        return content if content is not None else ""

    def __process_uncovered_pages(
        self, covered_pages: Set[int], page_manager: PageManager
    ) -> List[Section]:
        """Create `Section` objects for pages not covered by the TOC."""
        sections = []
        for page_num in range(1, page_manager.total_pages + 1):
            if page_num not in covered_pages:
                try:
                    section = self.__create_page_section(
                        page_num, page_manager
                    )
                    if section:
                        sections.append(section)
                except Exception as e:
                    print(
                        f"Error processing uncovered page {page_num}: {e}"
                    )
                    # Continue with next page instead of failing
                    continue
        return sections

    def __create_page_section(
        self, page_num: int, page_manager: PageManager
    ) -> Optional[Section]:
        """Build a comprehensive `Section` for a single page with all
        content types."""
        # Get comprehensive content including tables, images, etc.
        content = page_manager.get_comprehensive_page_content(
            page_num
        )
        if content is None:
            content = ""
        if not content or not content.strip():
            return None
        
        # Enhanced heading detection with multiple strategies
        heading = self.__detect_enhanced_heading(content, page_num)
        
        return self.__section_builder.build_comprehensive_page_section(
            page_num, content, heading
        )

    def __save_sections(
        self, sections: List[Section], output_file: str
    ) -> None:
        """Sort and save the final list of `Section` objects to JSONL file.
        """
        sections.sort(key=lambda s: (s.page, s.section_id or ""))
        section_dicts = [asdict(section) for section in sections]
        self.__file_handler.write_jsonl(output_file, section_dicts)

    def __finalize_parsing(self, sections: List[Section]) -> None:
        """Update the status and counters to finalize parsing process
        with enhanced reporting."""
        self._set_status("completed")
        self._increment_processed()
        
        # Calculate comprehensive coverage statistics
        coverage_stats = self.__calculate_parsing_coverage(sections)
        
        # Store coverage statistics (removed verbose output)
        self.__coverage_stats = coverage_stats

    def __extract_content_based_sections(
        self, pages_data: List[Dict[str, Any]], page_manager: PageManager,
        existing_sections: List[Section]
    ) -> List[Section]:
        """Extract genuine content-based sections from pages with
        substantial content."""
        content_sections = []
        existing_pages = {section.page for section in existing_sections}
        
        # Process pages with substantial content that aren't covered
        for page_data in pages_data:
            page_num = page_data.get('page', 0)
            if page_num > 0 and page_num not in existing_pages:
                text = page_data.get('text', '')
                
                # Only create sections for pages with meaningful content
                # Substantial content threshold
                if len(text.strip()) > 100:
                    # Try to extract natural sections first
                    natural_sections = (
                        self.__extract_natural_sections_from_page(
                            page_num, text
                        )
                    )
                    if natural_sections:
                        content_sections.extend(natural_sections)
                    else:
                        # Fallback to single intelligent section
                        section = self.__create_intelligent_page_section(
                            page_num, text, page_manager
                        )
                        if section:
                            content_sections.append(section)
        
        return content_sections

    def __create_intelligent_page_section(
        self, page_num: int, text: str, page_manager: PageManager
    ) -> Optional[Section]:
        """Create a single, high-quality section from a page with
        substantial content."""
        # Look for natural content boundaries (paragraphs, sections)
        paragraphs = [
            p.strip() for p in text.split('\n\n')
            if len(p.strip()) > 50
        ]
        
        # Use the most substantial paragraph or the full text if no
        # good paragraphs
        if paragraphs:
            # Find the longest meaningful paragraph
            main_content = max(paragraphs, key=len)
            if (len(main_content) < 200 and
                    len(text.strip()) > len(main_content)):
                # Use more of the page content
                main_content = text.strip()[:1000]
        else:
            main_content = text.strip()[:1000]
        
        # Detect a meaningful heading
        heading = self.__detect_enhanced_heading(
            main_content, page_num
        )
        if not heading or len(heading) < 5:
            # Look for technical keywords to create a descriptive title
            usb_keywords = [
                'usb', 'power', 'delivery', 'voltage', 'current', 'protocol'
            ]
            if any(keyword in text.lower() for keyword in usb_keywords):
                heading = f"USB Power Delivery Content - Page {page_num}"
            else:
                spec_keywords = ['specification', 'requirement', 'standard']
                if any(keyword in text.lower() for keyword in spec_keywords):
                    heading = f"Technical Specification - Page {page_num}"
                else:
                    heading = f"Document Content - Page {page_num}"
        
        return self.__section_builder.build_comprehensive_page_section(
            page_num, main_content, heading
        )

    def __extract_natural_sections_from_page(
        self, page_num: int, text: str
    ) -> List[Section]:
        """Extract natural sections from a page based on content
        structure."""
        sections = []
        
        # Look for natural section breaks (headings, numbered items)
        lines = text.split('\n')
        current_section = []
        section_heading = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line looks like a heading
            if self.__looks_like_heading(line):
                # Save previous section if it has content
                if current_section and section_heading:
                    content = '\n'.join(current_section)
                    if len(content.strip()) > 100:
                        section = (
                            self.__section_builder
                            .build_comprehensive_page_section(
                                page_num, content, section_heading
                            )
                        )
                        if section:
                            sections.append(section)
                
                # Start new section
                section_heading = line
                current_section = []
            else:
                current_section.append(line)
        
        # Don't forget the last section
        if current_section and section_heading:
            content = '\n'.join(current_section)
            if len(content.strip()) > 100:
                section = (
                    self.__section_builder
                    .build_comprehensive_page_section(
                        page_num, content, section_heading
                    )
                )
                if section:
                    sections.append(section)
        
        return sections
    
    def __looks_like_heading(self, line: str) -> bool:
        """Determine if a line looks like a section heading."""
        if not line or len(line) > 100:
            return False
            
        # Check for numbered headings (1.1, 2.3.4, etc.)
        if re.match(r'^\d+(\.\d+)*\s+', line):
            return True
            
        # Check for lettered headings (A.1, B.2, etc.)
        if re.match(r'^[A-Z](\.\d+)*\s+', line):
            return True
            
        # Check for all caps short lines
        if line.isupper() and len(line.split()) <= 6:
            return True
            
        # Check for lines ending with colon
        if line.endswith(':') and len(line.split()) <= 8:
            return True
            
        return False


    def __detect_enhanced_heading(
        self, content: str, page_num: int
    ) -> Optional[str]:
        """Enhanced heading detection using multiple strategies and
        content analysis."""
        if not content:
            return f"Content from Page {page_num}"
            
        lines = content.split('\n')
        
        # Try existing heading detector first
        for line in lines[:10]:  # Check first 10 lines
            if line is not None:
                heading = self.__heading_detector.detect_heading(line)
                if heading:
                    return heading
        
        # Fallback: Look for lines that appear to be headings
        for line in lines[:5]:  # Check first 5 lines
            if line is not None:
                line = line.strip()
                # Reasonable heading length
                if line and len(line) < 100:
                    # Check if line has heading characteristics
                    # Check if line has heading characteristics
                    if (line.isupper() or
                            any(char.isdigit() for char in line[:10]) or
                            line.count(' ') <= 8):  # Not too many words
                        return line
        
        # Last resort: Use page number as identifier
        return f"Content from Page {page_num}"
    
    def __calculate_parsing_coverage(
        self, sections: List[Section]
    ) -> Dict[str, Any]:
        """Calculate comprehensive coverage statistics for parsed
        sections."""
        stats = {
            'total_sections': len(sections),
            'toc_sections': 0,
            'non_toc_sections': 0,
            'sections_with_tables': 0,
            'sections_with_images': 0,
            'total_content_length': 0,
            'pages_covered': set(),
            'content_types_found': set()
        }
        
        for section in sections:
            # Count section types
            if hasattr(section, 'section_id') and section.section_id:
                stats['toc_sections'] += 1
            else:
                stats['non_toc_sections'] += 1
            
            # Track pages covered
            if hasattr(section, 'page'):
                stats['pages_covered'].add(section.page)
            
            # Analyze content
            content = getattr(section, 'content', '')
            if content:
                stats['total_content_length'] += len(content)
                
                # Check for tables and images in content
                if 'table' in content.lower() or '|' in content:
                    stats['sections_with_tables'] += 1
                    stats['content_types_found'].add('tables')
                
                image_words = ['image', 'figure', 'diagram']
                if any(word in content.lower() for word in image_words):
                    stats['sections_with_images'] += 1
                    stats['content_types_found'].add('images')
        
        # Convert set to count for final stats
        stats['pages_covered'] = len(stats['pages_covered'])
        stats['content_types_found'] = list(stats['content_types_found'])
        
        return stats


if __name__ == "__main__":
    print("Enhanced SectionParser module is ready for use.")
