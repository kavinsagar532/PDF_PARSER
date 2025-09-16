"""PDF text extraction with improved OOP design."""

# Standard library imports
from typing import Any, Dict, List, Optional

# Third-party imports
import pdfplumber

# Local imports
from base_classes import BaseProcessor
from helpers import JSONLHandler
from interfaces import ExtractorInterface


class PDFExtractor(BaseProcessor, ExtractorInterface):
    """Enhanced PDF text extractor with better encapsulation."""
    
    def __init__(self, pdf_path: str):
        super().__init__("PDFExtractor")
        self._pdf_path = self._validate_pdf_path(pdf_path)
        self._file_handler = JSONLHandler()
        self._total_pages = None
        self._extraction_config = self._initialize_config()
    
    @property
    def pdf_path(self) -> str:
        """Get PDF file path."""
        return self._pdf_path
    
    @property
    def total_pages(self) -> int:
        """Get total number of pages in PDF."""
        if self._total_pages is None:
            self._total_pages = self._calculate_total_pages()
        return self._total_pages
    
    @property
    def is_valid_pdf(self) -> bool:
        """Check if PDF is valid and readable."""
        try:
            return self._check_pdf_validity()
        except Exception:
            return False
    
    def extract_text(self, start_page: Optional[int] = 1, 
                    end_page: Optional[int] = None) -> List[Dict]:
        """Extract text from specified page range with validation."""
        self._set_status("extracting")
        
        try:
            pages_data = self._perform_extraction(start_page, end_page)
            self._set_status("completed")
            return pages_data
        except Exception as e:
            self._handle_extraction_error(e)
            return []
    
    def extract_all_pages(self) -> List[Dict]:
        """Extract text from all pages."""
        return self.extract_text()
    
    def save_to_file(self, data: List[Dict], file_path: str) -> int:
        """Save extracted pages to JSONL file."""
        return self._file_handler.write_jsonl(file_path, data)
    
    def dump_all_pages_jsonl(self, out_path: str = "usb_pd_pages.jsonl") -> int:
        """Extract all pages and save to file in one operation."""
        pages_data = self.extract_all_pages()
        return self.save_to_file(pages_data, out_path)
    
    def _initialize_config(self) -> Dict[str, Any]:
        """Initialize extraction configuration."""
        return {
            "extract_images": False,
            "extract_tables": False,
            "preserve_formatting": True
        }
    
    def _validate_pdf_path(self, pdf_path: str) -> str:
        """Validate PDF file path."""
        if not pdf_path or not isinstance(pdf_path, str):
            raise ValueError("Invalid PDF path")
        return pdf_path
    
    def _check_pdf_validity(self) -> bool:
        """Check if PDF file is valid and readable."""
        with pdfplumber.open(self._pdf_path) as pdf:
            return len(pdf.pages) > 0
    
    def _calculate_total_pages(self) -> int:
        """Calculate total number of pages."""
        try:
            with pdfplumber.open(self._pdf_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            print(f"Error calculating total pages: {e}")
            return 0
    
    def _perform_extraction(self, start_page: Optional[int], 
                          end_page: Optional[int]) -> List[Dict]:
        """Perform the actual text extraction."""
        with pdfplumber.open(self._pdf_path) as pdf:
            page_range = self._calculate_page_range(pdf, start_page, end_page)
            return self._extract_pages_in_range(pdf, page_range)
    
    def _calculate_page_range(self, pdf, start_page: Optional[int], 
                            end_page: Optional[int]) -> tuple:
        """Calculate the actual page range for extraction."""
        total = len(pdf.pages)
        
        if end_page is None or end_page > total:
            end_page = total
        
        start_idx = max(1, start_page or 1) - 1
        return start_idx, end_page
    
    def _extract_pages_in_range(self, pdf, page_range: tuple) -> List[Dict]:
        """Extract text from pages in specified range."""
        pages_data = []
        start_idx, end_page = page_range
        
        for i in range(start_idx, end_page):
            try:
                page_data = self._extract_single_page(pdf, i)
                pages_data.append(page_data)
                self._increment_processed()
            except Exception as e:
                self._handle_page_extraction_error(i, e)
                continue
        
        return pages_data
    
    def _extract_single_page(self, pdf, page_index: int) -> Dict[str, Any]:
        """Extract text from a single page."""
        page = pdf.pages[page_index]
        text = page.extract_text() or ""
        
        return {
            "page": page_index + 1,
            "text": text
        }
    
    def _handle_extraction_error(self, error: Exception) -> None:
        """Handle general extraction errors."""
        self._set_status("error")
        self._increment_errors()
        print(f"Error extracting text: {error}")
    
    def _handle_page_extraction_error(self, page_index: int, 
                                    error: Exception) -> None:
        """Handle individual page extraction errors."""
        self._increment_errors()
        print(f"Error extracting page {page_index + 1}: {error}")


if __name__ == "__main__":
    extractor = PDFExtractor("USB_PD_R3_2 V1.1 2024-10.pdf")
    n = extractor.dump_all_pages_jsonl()
    print(f"Dumped {n} pages to usb_pd_pages.jsonl")
