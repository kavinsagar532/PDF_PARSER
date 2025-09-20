"""Enhanced interfaces with improved separation of concerns and reduced coupling."""

# Standard library imports
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Iterable, List, Optional, Protocol


class Configurable(Protocol):
    """Protocol for configurable components."""
    
    def configure(self, **kwargs) -> None:
        """Configure the component."""
        ...
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        ...


class Cacheable(Protocol):
    """Protocol for components that support caching."""
    
    def enable_cache(self) -> None:
        """Enable caching."""
        ...
    
    def disable_cache(self) -> None:
        """Disable caching."""
        ...
    
    def clear_cache(self) -> None:
        """Clear cached data."""
        ...


class Loggable(Protocol):
    """Protocol for components with logging capabilities."""
    
    def set_log_level(self, level: str) -> None:
        """Set logging level."""
        ...


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


class TextProcessorInterface(ABC):
    """Interface for text processing utilities."""
    
    @abstractmethod
    def split_into_lines(self, text: str) -> List[str]:
        """Split text into lines."""
        raise NotImplementedError
    
    @abstractmethod
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        raise NotImplementedError
    
    @abstractmethod
    def extract_numbers(self, text: str) -> List[int]:
        """Extract numbers from text."""
        raise NotImplementedError


class ValidationInterface(ABC):
    """Interface for validation operations."""
    
    @abstractmethod
    def validate_required_fields(self, data: Dict[str, Any], 
                                required_fields: List[str]) -> List[str]:
        """Validate required fields."""
        raise NotImplementedError
    
    @abstractmethod
    def validate_data_types(self, data: Dict[str, Any], 
                           type_specs: Dict[str, type]) -> List[str]:
        """Validate data types."""
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


class ReportInterface(ABC):
    """Interface for report generation components."""
    
    @abstractmethod
    def generate_report(self, output_file: str) -> Dict[str, Any]:
        """Generate and save validation report."""
        raise NotImplementedError
    
    @abstractmethod
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate processing statistics."""
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
    
    @property
    @abstractmethod
    def results(self) -> Dict[str, Any]:
        """Get pipeline execution results."""
        raise NotImplementedError


# Type aliases for commonly used types
PageData = Dict[str, Any]
TOCEntry = Dict[str, Any]
SectionData = Dict[str, Any]
MetadataDict = Dict[str, Any]
ValidationResult = Dict[str, Any]
