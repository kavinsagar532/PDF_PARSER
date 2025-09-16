"""Metadata extraction with improved OOP design."""

# Standard library imports
from typing import Any, Dict, List

# Local imports
from base_classes import BaseParser
from extractor import PDFExtractor
from helpers import JSONLHandler
from interfaces import MetadataParserInterface
from text_utils import TextProcessor


class MetadataParser(BaseParser, MetadataParserInterface):
    """Enhanced metadata parser with better encapsulation."""
    
    def __init__(self, pdf_file: str, 
                 output_file: str = "usb_pd_metadata.jsonl"):
        super().__init__("MetadataParser")
        self._pdf_file = pdf_file
        self._output_file = output_file
        self._extractor = PDFExtractor(pdf_file)
        self._file_handler = JSONLHandler()
        self._text_processor = TextProcessor()
        self._metadata_patterns = self._initialize_patterns()
        self._extraction_config = self._initialize_extraction_config()
    
    @property
    def pdf_file(self) -> str:
        """Get PDF file path."""
        return self._pdf_file
    
    @property
    def output_file(self) -> str:
        """Get output file path."""
        return self._output_file
    
    @output_file.setter
    def output_file(self, value: str) -> None:
        """Set output file path with validation."""
        if not self._is_valid_file_path(value):
            raise ValueError("Invalid output file path")
        self._output_file = value
    
    def parse(self, input_data: Any = None) -> Dict[str, Any]:
        """Parse method implementation for base interface."""
        return self.parse_metadata()
    
    def validate_input(self, input_data: Any = None) -> bool:
        """Validate that PDF extractor is ready."""
        return self._extractor.is_valid_pdf
    
    def parse_metadata(self) -> Dict[str, Any]:
        """Extract and parse document metadata."""
        self._set_status("parsing")
        
        try:
            if self._should_validate_input() and not self.validate_input():
                raise ValueError("Invalid PDF file")
            
            metadata = self._extract_metadata()
            self._save_metadata(metadata)
            self._finalize_parsing()
            
            return metadata
            
        except Exception as e:
            self._handle_parsing_error(e, "metadata extraction")
            return {}
    
    def _initialize_patterns(self) -> Dict[str, str]:
        """Initialize regex patterns for metadata extraction."""
        return {
            "doc_title": (r"(Universal Serial Bus.*"
                         r"Power Delivery Specification)"),
            "revision": r"(?:Revision|Rev\.?)[: ]+\s*([0-9.]+)",
            "version": r"(?:Version|V)\s*[:]?[\s]*([0-9.]+)",
            "release_date": (r"(?:Release Date|Published:?)\s*[:]?[\s]*"
                           r"([0-9]{4}(?:-[0-9]{1,2})?)")
        }
    
    def _initialize_extraction_config(self) -> Dict[str, Any]:
        """Initialize metadata extraction configuration."""
        return {
            "start_page": 1,
            "end_page": 5,
            "default_value": "Unknown"
        }
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from PDF pages."""
        pages_data = self._extract_relevant_pages()
        combined_text = self._combine_page_text(pages_data)
        return self._extract_metadata_fields(combined_text)
    
    def _extract_relevant_pages(self) -> List[Dict]:
        """Extract pages relevant for metadata."""
        config = self._extraction_config
        return self._extractor.extract_text(
            start_page=config["start_page"],
            end_page=config["end_page"]
        )
    
    def _combine_page_text(self, pages_data: List[Dict]) -> str:
        """Combine text from multiple pages."""
        return "\n".join([page.get("text", "") for page in pages_data])
    
    def _extract_metadata_fields(self, text: str) -> Dict[str, Any]:
        """Extract metadata fields using configured patterns."""
        metadata = {}
        
        for field_name, pattern in self._metadata_patterns.items():
            metadata[field_name] = self._extract_single_field(
                pattern, text, field_name
            )
        
        return metadata
    
    def _extract_single_field(self, pattern: str, text: str, 
                             field_name: str) -> str:
        """Extract a single metadata field."""
        default_value = self._extraction_config["default_value"]
        return self._text_processor.extract_field_with_regex(
            pattern, text, default=default_value
        )
    
    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata to output file."""
        self._file_handler.write_jsonl(self._output_file, [metadata], mode="w")
    
    def _finalize_parsing(self) -> None:
        """Finalize the parsing process."""
        self._set_status("completed")
        self._increment_processed()
        print(f"Metadata extracted and saved to {self._output_file}")
    
    def _should_validate_input(self) -> bool:
        """Check if input validation should be performed."""
        return self.validation_enabled
    
    def _is_valid_file_path(self, file_path: str) -> bool:
        """Check if file path is valid."""
        return file_path and isinstance(file_path, str)


if __name__ == "__main__":
    parser = MetadataParser("USB_PD_R3_2 V1.1 2024-10.pdf")
    parser.parse_metadata()
