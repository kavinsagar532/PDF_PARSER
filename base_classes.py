"""Base classes providing common functionality."""

# Standard library imports
from abc import ABC
from typing import Any, Dict, Optional


# Local imports
from interfaces import ParserInterface, ProcessorInterface


class BaseProcessor(ProcessorInterface): 
    """Base class for all processing components."""
    
    def __init__(self, name: Optional[str] = None):
        self._name = name or self.__class__.__name__
        self._status = "initialized"
        self._error_count = 0
        self._processed_count = 0
    
    @property
    def name(self) -> str:
        """Get processor name."""
        return self._name
    
    @property
    def status(self) -> str:
        """Get current processing status."""
        return self._status
    
    @property
    def error_count(self) -> int:
        """Get number of errors encountered."""
        return self._error_count
    
    @property
    def processed_count(self) -> int:
        """Get number of items processed."""
        return self._processed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "name": self._name,
            "status": self._status,
            "processed_count": self._processed_count,
            "error_count": self._error_count
        }
    
    def _set_status(self, status: str) -> None:
        """Set processing status."""
        self._status = status
    
    def _increment_processed(self) -> None:
        """Increment processed item counter."""
        self._processed_count += 1
    
    def _increment_errors(self) -> None:
        """Increment error counter."""
        self._error_count += 1
    
    def _reset_counters(self) -> None:
        """Reset processing counters."""
        self._processed_count = 0
        self._error_count = 0


class BaseParser(BaseProcessor, ParserInterface):
    """Base class for all parser components."""
    
    def __init__(self, name: Optional[str] = None):
        super().__init__(name)
        self._validation_enabled = True
    
    @property
    def validation_enabled(self) -> bool:
        """Check if input validation is enabled."""
        return self._validation_enabled
    
    def disable_validation(self) -> None:
        """Disable input validation for performance."""
        self._validation_enabled = False
    
    def enable_validation(self) -> None:
        """Enable input validation."""
        self._validation_enabled = True
    
    def validate_input(self, input_data: Any) -> bool:
        """Default validation - always returns True."""
        if not self._validation_enabled:
            return True
        return input_data is not None
    
    def _handle_parsing_error(self, error: Exception, context: str) -> None:
        """Handle parsing errors consistently."""
        self._increment_errors()
        self._set_status("error")
        print(f"Error in {context}: {error}")
