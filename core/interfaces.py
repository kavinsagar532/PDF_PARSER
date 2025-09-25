"""Core interfaces defining contracts for all PDF parser components.

This module uses the Abstract Base Class (ABC) pattern to establish a
polymorphic design, ensuring that all major components of the PDF parsing
system adhere to a consistent API.
"""

# Standard library imports
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Iterable, List, Optional


class ProcessorInterface(ABC):
    """An interface for component that processes data and tracks status."""

    @abstractmethod
    def __init__(self, name: Optional[str] = None):
        """Initialize the processor with an optional name."""
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> str:
        """Return the current status (e.g., 'initialized', 'running')."""
        raise NotImplementedError

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Return a dictionary of processing statistics."""
        raise NotImplementedError


class ExtractorInterface(ABC):
    """An interface for components that extract data from a source file."""

    @abstractmethod
    def __init__(self, pdf_path: str):
        """Initialize the extractor with the path to the PDF file."""
        raise NotImplementedError

    @abstractmethod
    def extract_text(
        self, start_page: int, end_page: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Extract text from a specified page range.

        Args:
            start_page: The first page to extract (1-indexed).
            end_page: The last page extract. If None, extracts to the end.

        Returns:
            A list of dictionaries, where each dictionary.
        """
        raise NotImplementedError

    @abstractmethod
    def extract_all_pages(self) -> List[Dict[str, Any]]:
        """Extract text from all pages in the document."""
        raise NotImplementedError

    @property
    @abstractmethod
    def total_pages(self) -> int:
        """Return the total number of pages in the document."""
        raise NotImplementedError


class ParserInterface(ABC):
    """A base interface for all parsing components that transform data."""

    @abstractmethod
    def parse(self, input_data: Any) -> Any:
        """Parse the input data and return a structured output."""
        raise NotImplementedError

    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """Validate that the input data is suitable for parsing."""
        raise NotImplementedError


class MetadataParserInterface(ParserInterface):
    """An interface for components that parse document metadata."""

    @abstractmethod
    def parse_metadata(self) -> Dict[str, Any]:
        """Extract and parse document metadata into a dictionary."""
        raise NotImplementedError


class TOCParserInterface(ParserInterface):
    """An interface for components that parse the Table of Contents."""

    @abstractmethod
    def parse_toc(
        self, pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse the Table of Contents from a list of page data."""
        raise NotImplementedError


class SectionParserInterface(ParserInterface):
    """An interface for components that parse document sections."""

    @abstractmethod
    def parse_sections(
        self, toc_entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse document sections using TOC entries as a guide."""
        raise NotImplementedError


class HeadingStrategyInterface(ABC):
    """An interface for a single strategy to detect headings in text."""

    @abstractmethod
    def matches(self, text_line: str) -> bool:
        """Return True if the line is a heading by this strategy."""
        raise NotImplementedError

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Return the unique name of this strategy."""
        raise NotImplementedError

    @abstractmethod
    def get_confidence(self, text_line: str) -> float:
        """Return a confidence score (0.0 to 1.0) for the match."""
        raise NotImplementedError


class FileIOInterface(ABC):
    """An interface for file input/output operations."""

    @abstractmethod
    def read_jsonl(
        self, file_path: str
    ) -> Generator[Dict[str, Any], None, None]:
        """Read a JSONL file and yield records as dictionaries."""
        raise NotImplementedError

    @abstractmethod
    def write_jsonl(
        self,file_path:str,data: Iterable[Dict[str, Any]], mode: str = "w"
    ) -> int:
        """Write an iterable of dictionaries to a JSONL file."""
        raise NotImplementedError


class ValidatorInterface(ABC):
    """An interface for components that perform validation and reporting."""

    @abstractmethod
    def generate_report(self) -> Dict[str, Any]:
        """Generate a validation report."""
        raise NotImplementedError

    @abstractmethod
    def validate_data(self, data: Any) -> Dict[str, Any]:
        """Validate a given set of processed data."""
        raise NotImplementedError


class PipelineInterface(ABC):
    """An interface for the main end-to-end processing pipeline."""

    @abstractmethod
    def run_pipeline(self) -> None:
        """Execute the complete processing pipeline from start to finish."""
        raise NotImplementedError

    @property
    @abstractmethod
    def pipeline_status(self) -> Dict[str, Any]:
        """Return the current status of the pipeline."""
        raise NotImplementedError
