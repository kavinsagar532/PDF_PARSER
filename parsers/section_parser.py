"""A module for parsing the main sections of a document.

This module provides the `SectionParser` class, as an orchestrator
for the entire section parsing workflow. It coordinates a variety of helper
components to identify, extract, and structure the document's content.
"""

# Standard library imports
import os
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
        
        # Composition of helper components
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
        pages_data = list(self.__file_handler.read_jsonl(self.__pages_file))
        toc_data = (
            toc_entries if toc_entries is not None
            else list(self.__file_handler.read_jsonl(self.__toc_file))
        )
        return pages_data, toc_data

    def __process_all_sections(
        self, pages_data: List[Dict[str, Any]],
        toc_data: List[Dict[str, Any]]
    ) -> List[Section]:
        """Coordinate the processing of TOC-based and non-TOC pages."""
        page_manager = PageManager(pages_data)
        valid_toc = self.__toc_processor.validate_toc_entries(toc_data)
        
        toc_sections = self.__process_toc_sections(valid_toc, page_manager)
        
        covered_pages = self.__toc_processor.calculate_page_coverage(
            valid_toc, page_manager.total_pages
        )
        page_sections = self.__process_uncovered_pages(
            covered_pages, page_manager
        )
        
        return toc_sections + page_sections

    def __process_toc_sections(
        self, toc_entries: List[Dict[str, Any]], page_manager: PageManager
    ) -> List[Section]:
        """Build `Section` objects for each entry in the TOC."""
        sections = []
        for i, entry in enumerate(toc_entries):
            content = self.__extract_section_content(
                entry, toc_entries, i, page_manager
            )
            section = self.__section_builder.build_from_toc_entry(
                entry, content
            )
            sections.append(section)
        return sections

    def __extract_section_content(
        self, entry: Dict[str, Any], all_entries: List[Dict[str, Any]],
        current_index: int, page_manager: PageManager
    ) -> str:
        """Determine the page range for a TOC entry and extract content."""
        start_page = int(entry["page"])
        end_page = page_manager.total_pages
        if current_index + 1 < len(all_entries):
            end_page = int(all_entries[current_index + 1]["page"]) - 1
        return page_manager.get_content_range(start_page, end_page)

    def __process_uncovered_pages(
        self, covered_pages: Set[int], page_manager: PageManager
    ) -> List[Section]:
        """Create `Section` objects for pages not covered by the TOC."""
        sections = []
        for page_num in range(1, page_manager.total_pages + 1):
            if page_num not in covered_pages:
                section = self.__create_page_section(page_num, page_manager)
                if section:
                    sections.append(section)
        return sections

    def __create_page_section(
        self, page_num: int, page_manager: PageManager
    ) -> Optional[Section]:
        """Build a `Section` for a single page, detecting its heading."""
        content = page_manager.get_page_content(page_num).strip()
        if not content:
            return None
        
        heading = self.__heading_detector.detect_heading(content)
        return self.__section_builder.build_page_section(
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
        """Update the status and counters to finalize parsing process."""
        self._set_status("completed")
        self._increment_processed()
        print(f"Parsed {len(sections)} sections and saved to output file.")


if __name__ == "__main__":
    print("SectionParser module is ready for use.")
