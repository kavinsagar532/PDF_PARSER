"""A module for parsing metadata from a PDF document.

This module provides the `MetadataParser` class, which is  to extract
key metadata fields (like title, revision, and date) from the initial pages
of a PDF file. It leverages a combination of text extraction and regex
matching to achieve this.
"""

# Standard library imports
from typing import Any, Dict, List

# Local imports
from core.base_classes import BaseParser
from parsers.extractor import PDFExtractor
from utils.helpers import JSONLHandler
from core.interfaces import MetadataParserInterface
from utils.text_utils import TextProcessor


class MetadataParser(BaseParser, MetadataParserInterface):
    """Parses document metadata with a focus on encapsulation.

    This class inherits from `BaseParser` to gain tracking and implements
    the `MetadataParserInterface` to ensure a consistent API. All internal
    attributes and helper methods are private.
    """

    def __init__(
        self, pdf_file: str, output_file: str = "usb_pd_metadata.jsonl"
    ):
        super().__init__("MetadataParser")
        self.__pdf_file = pdf_file
        self.__output_file = output_file
        self.__extractor = PDFExtractor(pdf_file)
        self.__file_handler = JSONLHandler()
        self.__text_processor = TextProcessor()
        self.__metadata_patterns = self.__initialize_patterns()
        self.__extraction_config = self.__initialize_extraction_config()

    @property
    def pdf_file(self) -> str:
        """Return the path to the source PDF file."""
        return self.__pdf_file

    @property
    def output_file(self) -> str:
        """Return the path to the output JSONL file."""
        return self.__output_file

    @output_file.setter
    def output_file(self, value: str) -> None:
        """Set the output file path after validation."""
        if not self.__is_valid_file_path(value):
            raise ValueError("Output file path must be a non-empty string.")
        self.__output_file = value

    def parse(self, input_data: Any = None) -> Dict[str, Any]:
        """Implement the abstract `parse` method from `ParserInterface`."""
        return self.parse_metadata()

    def validate_input(self, input_data: Any = None) -> bool:
        """Validate that the PDF file is accessible and valid."""
        return self.__extractor.is_valid_pdf

    def parse_metadata(self) -> Dict[str, Any]:
        """Orchestrate the metadata extraction and parsing process."""
        self._set_status("parsing")
        try:
            if self.validation_enabled and not self.validate_input():
                raise ValueError(
                    "Input validation failed: Invalid PDF file."
                )
            
            metadata = self.__extract_metadata()
            self.__save_metadata(metadata)
            self.__finalize_parsing()
            return metadata
        except Exception as e:
            self._handle_parsing_error(e, "metadata extraction")
            return {}

    def __initialize_patterns(self) -> Dict[str, str]:
        """Define the regex patterns for finding metadata fields."""
        return {
            "doc_title": (
                r"(Universal Serial Bus.*Power Delivery Specification)"
            ),
            "revision": r"(?:Revision|Rev\.?)[: ]+\s*([0-9.]+)",
            "version": r"(?:Version|V)\s*[:]?\s*([0-9.]+)",
            "release_date": (
                r"(?:Release Date|Published:?)\s*[:]?\s*"
                r"([0-9]{4}(?:-[0-9]{1,2})?)"
            ),
        }

    def __initialize_extraction_config(self) -> Dict[str, Any]:
        """Configure the parameters for the metadata extraction process."""
        return {"start_page": 1, "end_page": 5, "default_value": "Unknown"}

    def __extract_metadata(self) -> Dict[str, Any]:
        """Extract text from relevant pages and parse metadata fields."""
        pages_data = self.__extract_relevant_pages()
        combined_text = self.__combine_page_text(pages_data)
        return self.__extract_metadata_fields(combined_text)

    def __extract_relevant_pages(self) -> List[Dict[str, Any]]:
        """Extract text from the first few pages of the PDF."""
        config = self.__extraction_config
        return self.__extractor.extract_text(
            start_page=config["start_page"], end_page=config["end_page"]
        )

    def __combine_page_text(self, pages_data: List[Dict[str, Any]]) -> str:
        """Join the text from multiple pages into a single string."""
        return "\n".join(page.get("text", "") for page in pages_data)

    def __extract_metadata_fields(self, text: str) -> Dict[str, Any]:
        """Apply regex patterns to the text to find extract metadata."""
        metadata = {}
        for field_name, pattern in self.__metadata_patterns.items():
            metadata[field_name] = self.__extract_single_field(pattern, text)
        return metadata

    def __extract_single_field(self, pattern: str, text: str) -> str:
        """Extract a single metadata field using a regex pattern."""
        default_value = self.__extraction_config["default_value"]
        return self.__text_processor.extract_field_with_regex(
            pattern, text, default=default_value
        )

    def __save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save the extracted metadata to the output JSONL file."""
        self.__file_handler.write_jsonl(
            self.__output_file, [metadata], mode="w"
        )

    def __finalize_parsing(self) -> None:
        """Update the status and counters to finalize the parsing."""
        self._set_status("completed")
        self._increment_processed()
        # Metadata extraction completed

    def __is_valid_file_path(self, file_path: str) -> bool:
        """Check if the provided file path is a non-empty string."""
        return isinstance(file_path, str) and bool(file_path)


if __name__ == "__main__":
    parser = MetadataParser("USB_PD_R3_2 V1.1 2024-10.pdf")
    parser.parse_metadata()
