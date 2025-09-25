"""PDF text extraction component with a robust, object-oriented design.

This module provides the `PDFExtractor` class, which is responsible for
extracting text and metadata from PDF files using the `pdfplumber` library.
It adheres to a strict object-oriented structure with encapsulated attributes
and methods.
"""

# Standard library imports
from typing import Any, Dict, List, Optional

# Third-party imports
import pdfplumber

# Local imports
from core.base_classes import BaseProcessor
from utils.helpers import JSONLHandler
from core.interfaces import ExtractorInterface


class PDFExtractor(BaseProcessor, ExtractorInterface):
    """Extracts text from PDF files with strong encapsulation.

    This class implements both the `BaseProcessor` for status tracking and
    the `ExtractorInterface` for a consistent extraction API. All internal
    state and helper methods are private.
    """
    
    def __init__(self, pdf_path: str):
        super().__init__("PDFExtractor")
        self.__pdf_path = self.__validate_pdf_path(pdf_path)
        self.__file_handler = JSONLHandler()
        self.__total_pages: Optional[int] = None
        self.__extraction_config = self.__initialize_config()
    
    @property
    def pdf_path(self) -> str:
        """Return the path to the PDF file."""
        return self.__pdf_path
    
    @property
    def total_pages(self) -> int:
        """Return the total number of pages, calculated on first access."""
        if self.__total_pages is None:
            self.__total_pages = self.__calculate_total_pages()
        return self.__total_pages
    
    @property
    def is_valid_pdf(self) -> bool:
        """Return True if the PDF file is valid and can be opened."""
        try:
            return self.__check_pdf_validity()
        except Exception:
            return False
    
    def extract_text(
        self, start_page: int = 1, end_page: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extract text from a specified range of pages."""
        self._set_status("extracting")
        try:
            pages_data = self.__perform_extraction(start_page, end_page)
            self._set_status("completed")
            return pages_data
        except Exception as e:
            self.__handle_extraction_error(e)
            return []
    
    def extract_all_pages(self) -> List[Dict[str, Any]]:
        """Extract text from all pages of the document."""
        return self.extract_text(1, self.total_pages)
    
    def save_to_file(self, data: List[Dict[str, Any]], file_path: str) -> int:
        """Save a list of page data to a JSONL file."""
        return self.__file_handler.write_jsonl(file_path, data)
    
    def dump_all_pages_jsonl(
        self, path: str = "usb_pd_pages.jsonl"
    ) -> int:
        """Extract all pages and save them directly to a JSONL file."""
        pages_data = self.extract_all_pages()
        return self.save_to_file(pages_data, path)
    
    def __initialize_config(self) -> Dict[str, Any]:
        """Return the default configuration for text extraction."""
        return {
            "extract_images": False,
            "extract_tables": False,
            "preserve_formatting": True,
        }
    
    def __validate_pdf_path(self, pdf_path: str) -> str:
        """Validate that the PDF path is a non-empty string."""
        if not isinstance(pdf_path, str) or not pdf_path:
            raise ValueError("PDF path must be a non-empty string.")
        return pdf_path
    
    def __check_pdf_validity(self) -> bool:
        """Confirm the PDF can be opened and contains at least one page."""
        with pdfplumber.open(self.__pdf_path) as pdf:
            return len(pdf.pages) > 0
    
    def __calculate_total_pages(self) -> int:
        """Return the total number of pages in the PDF."""
        try:
            with pdfplumber.open(self.__pdf_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            print(f"Error calculating total pages: {e}")
            return 0
    
    def __perform_extraction(
        self, start_page: int, end_page: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Orchestrate the text extraction process."""
        with pdfplumber.open(self.__pdf_path) as pdf:
            page_range = self.__calculate_page_range(pdf, start_page, end_page)
            return self.__extract_pages_in_range(pdf, page_range)
    
    def __calculate_page_range(
        self, pdf, start_page: int, end_page: Optional[int]
    ) -> tuple[int, int]:
        """Calculate the 0-indexed start and end pages for iteration."""
        total = len(pdf.pages)
        final_end_page = total if end_page is None or end_page > total else end_page
        start_idx = max(0, start_page - 1)
        return start_idx, final_end_page
    
    def __extract_pages_in_range(
        self, pdf, page_range: tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """Iterate through a page range and extract text from each page."""
        pages_data = []
        start_idx, end_page = page_range
        for i in range(start_idx, end_page):
            try:
                page_data = self.__extract_single_page(pdf, i)
                pages_data.append(page_data)
                self._increment_processed()
            except Exception as e:
                self.__handle_page_extraction_error(i, e)
        return pages_data
    
    def __extract_single_page(
        self, pdf, page_index: int
    ) -> Dict[str, Any]:
        """Extract and structure the text content of a single page."""
        page = pdf.pages[page_index]
        text = page.extract_text() or ""
        return {"page": page_index + 1, "text": text}
    
    def __handle_extraction_error(self, error: Exception) -> None:
        """Log a general error that occurs during the extraction."""
        self._set_status("error")
        self._increment_errors()
        print(f"Error during PDF text extraction: {error}")
    
    def __handle_page_extraction_error(
        self, page_index: int, error: Exception
    ) -> None:
        """Log an error that occurs while processing a single page."""
        self._increment_errors()
        print(f"Error extracting page {page_index + 1}: {error}")


if __name__ == "__main__":
    extractor = PDFExtractor("USB_PD_R3_2 V1.1 2024-10.pdf")
    page_count = extractor.dump_all_pages_jsonl()
    print(f"Dumped {page_count} pages to usb_pd_pages.jsonl")
