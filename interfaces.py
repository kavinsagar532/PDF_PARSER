"""Core interfaces defining contracts for all PDF parser components."""

# Standard library imports
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Iterable, List, Optional


class ExtractorInterface(ABC):
    """Interface for PDF text extraction components."""
    
    @abstractmethod
    def extract_text(self, start_page: Optional[int] = 1, 
                    end_page: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract text from specified page range."""
        raise NotImplementedError
    
    @abstractmethod
    def extract_all_pages(self) -> List[Dict[str, Any]]:
        """Extract text from all pages."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def total_pages(self) -> int:
        """Get total number of pages."""
        raise NotImplementedError
    
    @abstractmethod
    def save_to_file(self, data: List[Dict], file_path: str) -> int:
        """Save extracted data to file."""
        raise NotImplementedError


class ParserInterface(ABC):
    """Base interface for all parsing components."""
    
    @abstractmethod
    def parse(self, input_data: Any) -> Any:
        """Parse input data and return structured output."""
        raise NotImplementedError
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data before processing."""
        raise NotImplementedError


class ProcessorInterface(ABC):
    """Interface for processing components with status tracking."""
    
    @property
    @abstractmethod
    def status(self) -> str:
        """Get current processing status."""
        raise NotImplementedError
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        raise NotImplementedError


class MetadataParserInterface(ParserInterface):
    """Interface for metadata parsing components."""
    
    @abstractmethod
    def parse_metadata(self) -> Dict[str, Any]:
        """Extract and parse document metadata."""
        raise NotImplementedError


class TOCParserInterface(ParserInterface):
    """Interface for Table of Contents parsing components."""
    
    @abstractmethod
    def parse_toc(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse table of contents from pages."""
        raise NotImplementedError


class SectionParserInterface(ParserInterface):
    """Interface for section parsing components."""
    
    @abstractmethod
    def parse_sections(self, toc_entries: Optional[List[Dict]] = None,
                      output_file: str = "sections.jsonl") -> List[Dict]:
        """Parse document sections."""
        raise NotImplementedError


class HeadingStrategyInterface(ABC):
    """Interface for heading detection strategies."""
    
    @abstractmethod
    def matches(self, text_line: str) -> bool:
        """Determine if a line represents a heading."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Get the name of this strategy."""
        raise NotImplementedError
    
    @abstractmethod
    def get_confidence(self, text_line: str) -> float:
        """Get confidence score for heading detection."""
        raise NotImplementedError


class FileIOInterface(ABC):
    """Interface for file input/output operations."""
    
    @abstractmethod
    def read_jsonl(self, file_path: str) -> Generator[Dict, None, None]:
        """Read JSONL file and yield records."""
        raise NotImplementedError
    
    @abstractmethod
    def write_jsonl(self, file_path: str, data: Iterable[Dict], 
                   mode: str = "w") -> int:
        """Write data to JSONL file."""
        raise NotImplementedError


class ValidatorInterface(ABC):
    """Interface for validation and report generation."""
    
    @abstractmethod
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        raise NotImplementedError
    
    @abstractmethod
    def validate_data(self, data: Any) -> Dict[str, Any]:
        """Validate processed data."""
        raise NotImplementedError


class PipelineInterface(ABC):
    """Interface for end-to-end processing pipelines."""
    
    @abstractmethod
    def run_pipeline(self) -> None:
        """Execute the complete processing pipeline."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        raise NotImplementedError
