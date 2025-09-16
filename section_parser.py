"""Section parsing with improved OOP design and SOLID principles."""

# Standard library imports
import os
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Set,Any

# Local imports
from base_classes import BaseParser
from heading_strategies import HeadingDetector
from helpers import JSONLHandler
from interfaces import SectionParserInterface


@dataclass
class Section:
    """Data class representing a document section."""
    doc_title: str
    section_id: str
    title: str
    full_path: str
    page: int
    level: int
    parent_id: Optional[str]
    tags: List[str]
    content: str


class PageManager:
    """Manages page data and content extraction."""
    
    def __init__(self, pages_data: List[Dict]):
        self._pages_by_number = self._organize_pages(pages_data)
        self._total_pages = len(pages_data)
    
    @property
    def total_pages(self) -> int:
        """Get total number of pages."""
        return self._total_pages
    
    def get_page_content(self, page_number: int) -> str:
        """Get content for a specific page."""
        return self._pages_by_number.get(page_number, "")
    
    def get_content_range(self, start_page: int, end_page: int) -> str:
        """Get combined content for a range of pages."""
        content_parts = [
            self.get_page_content(page_num) 
            for page_num in range(start_page, end_page + 1)
        ]
        return "\n".join(content_parts).strip()
    
    def _organize_pages(self, pages_data: List[Dict]) -> Dict[int, str]:
        """Organize pages data by page number."""
        return {
            page.get("page"): page.get("text", "") 
            for page in pages_data
        }


class TOCProcessor:
    """Processes Table of Contents entries."""
    
    def __init__(self):
        self._processed_entries = 0
    
    @property
    def processed_entries(self) -> int:
        """Get number of processed entries."""
        return self._processed_entries
    
    def validate_toc_entries(self, toc_entries: List[Dict]) -> List[Dict]:
        """Validate and filter TOC entries."""
        valid_entries = [
            entry for entry in toc_entries
            if self._is_valid_entry(entry)
        ]
        
        return sorted(valid_entries, key=lambda x: x["page"])
    
    def calculate_page_coverage(self, toc_entries: List[Dict], 
                              total_pages: int) -> Set[int]:
        """Calculate which pages are covered by TOC entries."""
        covered_pages = set()
        
        for i, entry in enumerate(toc_entries):
            page_range = self._calculate_entry_page_range(
                entry, toc_entries, i, total_pages
            )
            covered_pages.update(page_range)
            self._processed_entries += 1
        
        return covered_pages
    
    def _is_valid_entry(self, entry: Dict) -> bool:
        """Check if TOC entry is valid."""
        page = entry.get("page")
        return isinstance(page, int) and page > 0
    
    def _calculate_entry_page_range(self, entry: Dict, all_entries: List[Dict], 
                                  current_index: int, total_pages: int) -> range:
        """Calculate page range covered by a TOC entry."""
        start_page = int(entry["page"])
        
        if current_index + 1 < len(all_entries):
            end_page = int(all_entries[current_index + 1]["page"]) - 1
        else:
            end_page = total_pages
        
        end_page = max(end_page, start_page)
        return range(start_page, end_page + 1)


class SectionBuilder:
    """Builds section objects from TOC entries and page content."""
    
    def __init__(self, doc_title: str):
        self._doc_title = doc_title
        self._sections_created = 0
    
    @property
    def sections_created(self) -> int:
        """Get number of sections created."""
        return self._sections_created
    
    def build_from_toc_entry(self, entry: Dict, 
                           content: str) -> Section:
        """Build a section from a TOC entry."""
        section_metadata = self._extract_section_metadata(entry)
        
        section = Section(
            doc_title=entry.get("doc_title") or self._doc_title,
            section_id=section_metadata["section_id"],
            title=entry.get("title", ""),
            full_path=section_metadata["full_path"],
            page=int(entry["page"]),
            level=section_metadata["level"],
            parent_id=section_metadata["parent_id"],
            tags=entry.get("tags", []),
            content=content
        )
        
        self._sections_created += 1
        return section
    
    def build_page_section(self, page_number: int, content: str, 
                          heading: Optional[str] = None) -> Section:
        """Build a section for a standalone page."""
        title = heading or f"Page {page_number}"
        
        section = Section(
            doc_title=self._doc_title,
            section_id=f"Page-{page_number}",
            title=title,
            full_path=f"Page-{page_number} {title}",
            page=page_number,
            level=1,
            parent_id=None,
            tags=[],
            content=content
        )
        
        self._sections_created += 1
        return section
    
    def _extract_section_metadata(self, entry: Dict) -> Dict[str, Any]:
        """Extract section metadata from TOC entry."""
        section_id = entry.get("section_id", "")
        level = len(section_id.split(".")) if section_id else 1
        
        parent_id = None
        if section_id and "." in section_id:
            parent_id = ".".join(section_id.split(".")[:-1])
        
        full_path = f"{section_id} {entry.get('title', '')}".strip()
        
        return {
            "section_id": section_id,
            "level": level,
            "parent_id": parent_id,
            "full_path": full_path
        }


class SectionParser(BaseParser, SectionParserInterface):
    """Enhanced section parser with SOLID principles."""
    
    def __init__(self, pdf_path: str, toc_file: str = "usb_pd_toc.jsonl",
                 pages_file: str = "usb_pd_pages.jsonl", 
                 doc_title: str = "Universal Serial Bus Power Delivery Specification"):
        super().__init__("SectionParser")
        self._pdf_path = pdf_path
        self._toc_file = toc_file
        self._pages_file = pages_file
        self._doc_title = doc_title
        
        # Initialize components
        self._file_handler = JSONLHandler()
        self._heading_detector = HeadingDetector()
        self._toc_processor = TOCProcessor()
        self._section_builder = SectionBuilder(doc_title)
    
    @property
    def pdf_path(self) -> str:
        """Get PDF file path."""
        return self._pdf_path
    
    @property
    def doc_title(self) -> str:
        """Get document title."""
        return self._doc_title
    
    def parse(self, input_data: Optional[List[Dict]] = None) -> List[Dict]:
        """Parse method implementation for base interface."""
        return self.parse_sections(input_data)
    
    def validate_input(self, toc_entries: Optional[List[Dict]] = None) -> bool:
        """Validate input data and file dependencies."""
        if toc_entries is None:
            return self._validate_required_files()
        
        return isinstance(toc_entries, list)
    
    def parse_sections(self, toc_entries: Optional[List[Dict]] = None,
                      output_file: str = "usb_pd_spec.jsonl") -> List[Dict]:
        """Parse document sections with enhanced error handling."""
        self._set_status("parsing")
        
        try:
            # Load and validate data
            pages_data, toc_data = self._load_input_data(toc_entries)
            
            # Process sections
            all_sections = self._process_all_sections(pages_data, toc_data)
            
            # Save results
            self._save_sections(all_sections, output_file)
            self._finalize_parsing(all_sections)
            
            return [asdict(section) for section in all_sections]
            
        except Exception as e:
            self._handle_parsing_error(e, "section parsing")
            return []
    
    def _validate_required_files(self) -> bool:
        """Validate that required files exist."""
        return (os.path.exists(self._toc_file) and 
                os.path.exists(self._pages_file))
    
    def _load_input_data(self, toc_entries: Optional[List[Dict]]) -> tuple:
        """Load pages and TOC data."""
        pages_data = list(self._file_handler.read_jsonl(self._pages_file))
        
        if toc_entries is None:
            toc_data = list(self._file_handler.read_jsonl(self._toc_file))
        else:
            toc_data = toc_entries
        
        return pages_data, toc_data
    
    def _process_all_sections(self, pages_data: List[Dict], 
                            toc_data: List[Dict]) -> List[Section]:
        """Process both TOC-based and standalone sections."""
        # Initialize managers
        page_manager = PageManager(pages_data)
        
        # Process TOC-based sections
        valid_toc = self._toc_processor.validate_toc_entries(toc_data)
        toc_sections = self._process_toc_sections(valid_toc, page_manager)
        
        # Process uncovered pages
        covered_pages = self._toc_processor.calculate_page_coverage(
            valid_toc, page_manager.total_pages
        )
        page_sections = self._process_uncovered_pages(
            covered_pages, page_manager
        )
        
        return toc_sections + page_sections
    
    def _process_toc_sections(self, toc_entries: List[Dict], 
                            page_manager: PageManager) -> List[Section]:
        """Process sections based on TOC entries."""
        sections = []
        
        for i, entry in enumerate(toc_entries):
            content = self._extract_section_content(
                entry, toc_entries, i, page_manager
            )
            section = self._section_builder.build_from_toc_entry(entry, content)
            sections.append(section)
        
        return sections
    
    def _extract_section_content(self, entry: Dict, all_entries: List[Dict], 
                               current_index: int, 
                               page_manager: PageManager) -> str:
        """Extract content for a single section."""
        start_page = int(entry["page"])
        
        if current_index + 1 < len(all_entries):
            end_page = int(all_entries[current_index + 1]["page"]) - 1
        else:
            end_page = page_manager.total_pages
        
        end_page = max(end_page, start_page)
        return page_manager.get_content_range(start_page, end_page)
    
    def _process_uncovered_pages(self, covered_pages: Set[int], 
                               page_manager: PageManager) -> List[Section]:
        """Process pages not covered by TOC."""
        sections = []
        
        for page_num in range(1, page_manager.total_pages + 1):
            if self._should_process_page(page_num, covered_pages):
                section = self._create_page_section(page_num, page_manager)
                if section:
                    sections.append(section)
        
        return sections
    
    def _should_process_page(self, page_num: int, 
                           covered_pages: Set[int]) -> bool:
        """Check if page should be processed as standalone section."""
        return page_num not in covered_pages
    
    def _create_page_section(self, page_num: int, 
                           page_manager: PageManager) -> Optional[Section]:
        """Create section for a standalone page."""
        content = page_manager.get_page_content(page_num).strip()
        if not content:
            return None
        
        heading = self._heading_detector.detect_heading(content)
        return self._section_builder.build_page_section(
            page_num, content, heading
        )
    
    def _save_sections(self, sections: List[Section], 
                      output_file: str) -> None:
        """Save sections to output file."""
        # Sort sections by page and section ID
        sections.sort(key=lambda s: (s.page, s.section_id or ""))
        
        section_dicts = [asdict(section) for section in sections]
        self._file_handler.write_jsonl(output_file, section_dicts)
    
    def _finalize_parsing(self, sections: List[Section]) -> None:
        """Finalize parsing process."""
        self._set_status("completed")
        self._increment_processed()
        print(f"Parsed {len(sections)} sections into output file")


if __name__ == "__main__":
    print("SectionParser module ready")
