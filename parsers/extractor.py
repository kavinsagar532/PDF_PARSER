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
        """Return the enhanced configuration for comprehensive extraction."""
        return {
            "extract_images": True,
            "extract_tables": True,
            "preserve_formatting": True,
            "extract_layout": True,
            "extract_metadata": True,
            "extract_annotations": True,
            "use_layout_engine": True,
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
        final_end_page = (
            total if end_page is None or end_page > total else end_page
        )
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
        """Extract comprehensive content from a single page including
        text, tables, images."""
        page = pdf.pages[page_index]
        page_data = {"page": page_index + 1}
        
        # Enhanced text extraction with multiple methods
        page_data["text"] = self.__extract_comprehensive_text(page)
        
        # Extract tables if enabled
        if self.__extraction_config["extract_tables"]:
            page_data["tables"] = self.__extract_tables(page)
        
        # Extract images if enabled
        if self.__extraction_config["extract_images"]:
            page_data["images"] = self.__extract_images(page)
        
        # Extract layout information
        if self.__extraction_config["extract_layout"]:
            page_data["layout"] = self.__extract_layout_info(page)
        
        # Extract metadata and annotations
        if self.__extraction_config["extract_metadata"]:
            page_data["metadata"] = self.__extract_page_metadata(page)
        
        # Calculate content coverage metrics
        page_data["coverage_stats"] = self.__calculate_page_coverage(page_data)
        
        return page_data
    
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
    
    def __extract_comprehensive_text(self, page) -> str:
        """Extract text using multiple methods for maximum coverage."""
        text_methods = []
        
        # Method 1: Standard text extraction
        try:
            standard_text = page.extract_text() or ""
            if standard_text.strip():
                text_methods.append(standard_text)
        except Exception:
            pass
        
        # Method 2: Extract text with layout preservation
        try:
            layout_text = page.extract_text(layout=True) or ""
            if layout_text.strip() and layout_text != standard_text:
                text_methods.append(layout_text)
        except Exception:
            pass
        
        # Method 3: Character-level extraction for complex layouts
        try:
            chars = page.chars
            if chars:
                char_text = ''.join(char.get('text', '') for char in chars)
                if char_text.strip() and char_text not in text_methods:
                    text_methods.append(char_text)
        except Exception:
            pass
        
        # Method 4: Extract text from words (fallback)
        try:
            words = page.extract_words()
            if words:
                word_text = ' '.join(word.get('text', '') for word in words)
                if word_text.strip() and word_text not in text_methods:
                    text_methods.append(word_text)
        except Exception:
            pass
        
        # Combine all extracted text methods
        separator = '\n---EXTRACTION_METHOD_SEPARATOR---\n'
        combined_text = separator.join(text_methods)
        return combined_text or ""
    
    def __extract_tables(self, page) -> List[Dict[str, Any]]:
        """Extract all tables from the page."""
        tables_data = []
        try:
            tables = page.extract_tables()
            for i, table in enumerate(tables or []):
                if table:
                    table_data = {
                        "table_id": i + 1,
                        "rows": len(table),
                        "cols": len(table[0]) if table else 0,
                        "data": table,
                        "text_representation": self.__table_to_text(table)
                    }
                    tables_data.append(table_data)
        except Exception as e:
            print(f"Error extracting tables: {e}")
        
        return tables_data
    
    def __extract_images(self, page) -> List[Dict[str, Any]]:
        """Extract image information from the page."""
        images_data = []
        try:
            # Extract image objects
            if hasattr(page, 'images'):
                for i, img in enumerate(page.images or []):
                    image_data = {
                        "image_id": i + 1,
                        "bbox": img.get('bbox', []),
                        "width": img.get('width', 0),
                        "height": img.get('height', 0),
                        "object_type": img.get('object_type', 'image'),
                        "name": img.get('name', f'image_{i+1}')
                    }
                    images_data.append(image_data)
            
            # Also check for figures and drawings
            if hasattr(page, 'figures'):
                for i, fig in enumerate(page.figures or []):
                    figure_data = {
                        "figure_id": i + 1,
                        "bbox": fig.get('bbox', []),
                        "object_type": "figure",
                        "name": f"figure_{i+1}"
                    }
                    images_data.append(figure_data)
                    
        except Exception as e:
            print(f"Error extracting images: {e}")
        
        return images_data
    
    def __extract_layout_info(self, page) -> Dict[str, Any]:
        """Extract layout and formatting information."""
        layout_info = {}
        try:
            # Page dimensions
            layout_info["page_width"] = page.width
            layout_info["page_height"] = page.height
            
            # Text layout information
            layout_info["text_lines"] = []
            if hasattr(page, 'chars'):
                chars = page.chars or []
                layout_info["char_count"] = len(chars)
                
                # Group characters into lines
                lines = {}
                for char in chars:
                    y_pos = round(char.get('y0', 0), 1)
                    if y_pos not in lines:
                        lines[y_pos] = []
                    lines[y_pos].append(char)
                
                # Convert to structured line data
                for y_pos, line_chars in sorted(lines.items()):
                    line_text = ''.join(
                        char.get('text', '') for char in line_chars
                    )
                    if line_text.strip():
                        layout_info["text_lines"].append({
                            "y_position": y_pos,
                            "text": line_text.strip(),
                            "char_count": len(line_chars)
                        })
            
            # Extract rectangles and lines (visual elements)
            layout_info["visual_elements"] = {
                "rectangles": len(page.rects or []),
                "lines": len(page.lines or []),
                "curves": len(page.curves or [])
            }
            
        except Exception as e:
            print(f"Error extracting layout info: {e}")
        
        return layout_info
    
    def __extract_page_metadata(self, page) -> Dict[str, Any]:
        """Extract metadata and annotations from the page."""
        metadata = {}
        try:
            # Basic page properties
            metadata["rotation"] = getattr(page, 'rotation', 0)
            metadata["cropbox"] = getattr(page, 'cropbox', [])
            metadata["mediabox"] = getattr(page, 'mediabox', [])
            
            # Annotations
            if hasattr(page, 'annots'):
                annotations = page.annots or []
                metadata["annotations"] = []
                for annot in annotations:
                    annot_data = {
                        "type": annot.get('subtype', 'unknown'),
                        "content": annot.get('contents', ''),
                        "bbox": annot.get('rect', [])
                    }
                    metadata["annotations"].append(annot_data)
            
        except Exception as e:
            print(f"Error extracting page metadata: {e}")
        
        return metadata
    
    def __calculate_page_coverage(
        self, page_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate coverage statistics for the extracted page
        content."""
        stats = {
            "text_length": len(page_data.get("text", "")),
            "has_text": bool(page_data.get("text", "").strip()),
            "table_count": len(page_data.get("tables", [])),
            "image_count": len(page_data.get("images", [])),
            "annotation_count": len(
                page_data.get("metadata", {}).get("annotations", [])
            ),
            "visual_elements": page_data.get("layout", {}).get(
                "visual_elements", {}
            ),
            "coverage_score": 0.0
        }
        
        # Calculate overall coverage score
        score = 0.0
        if stats["has_text"]:
            score += 0.4
        if stats["table_count"] > 0:
            score += 0.2
        if stats["image_count"] > 0:
            score += 0.2
        if stats["annotation_count"] > 0:
            score += 0.1
        if sum(stats["visual_elements"].values()) > 0:
            score += 0.1
        
        stats["coverage_score"] = min(1.0, score)
        return stats
    
    def __table_to_text(self, table: List[List[str]]) -> str:
        """Convert table data to readable text format."""
        if not table:
            return ""
        
        text_lines = []
        for row in table:
            if row:
                # Join non-empty cells with | separator
                row_text = " | ".join(str(cell or "") for cell in row)
                if row_text.strip():
                    text_lines.append(row_text)
        
        return "\n".join(text_lines)


if __name__ == "__main__":
    extractor = PDFExtractor("USB_PD_R3_2 V1.1 2024-10.pdf")
    page_count = extractor.dump_all_pages_jsonl()
    print(f"Dumped {page_count} pages to usb_pd_pages.jsonl")
