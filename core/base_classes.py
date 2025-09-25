"""Base classes providing common functionality and enforcing OOP principles.

This module contains abstract and concrete base classes that offer shared
functionality like status tracking, error counting, and input validation.
They are designed to be extended by concrete parser processor components.
"""

# Standard library imports
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# Local imports
from core.interfaces import ParserInterface, ProcessorInterface


class BaseProcessor(ProcessorInterface):
    """A concrete base class for components that process data.

    This class provides a full implementation of the ProcessorInterface,
    offering status and statistics tracking. Attributes are encapsulated
    using a private (`__`) naming convention, with public properties for
    access.
    """

    def __init__(self, name: Optional[str] = None):
        self.__name = name or self.__class__.__name__
        self.__status = "initialized"
        self.__error_count = 0
        self.__processed_count = 0

    @property
    def name(self) -> str:
        """Return the name of the processor."""
        return self.__name

    @property
    def status(self) -> str:
        """Return the current processing status."""
        return self.__status

    @property
    def error_count(self) -> int:
        """Return the total number of errors encountered."""
        return self.__error_count

    @property
    def processed_count(self) -> int:
        """Return the total number of items successfully processed."""
        return self.__processed_count

    def get_stats(self) -> Dict[str, Any]:
        """Return a dictionary of the processor's current statistics."""
        return {
            "name": self.name,
            "status": self.status,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
        }

    def _set_status(self, status: str) -> None:
        """Set the processor's status. For internal use by subclasses."""
        self.__status = status

    def _increment_processed(self) -> None:
        """Increment the counter for processed items."""
        self.__processed_count += 1

    def _increment_errors(self) -> None:
        """Increment the counter for errors."""
        self.__error_count += 1

    def _reset_counters(self) -> None:
        """Reset the processed and error counters to zero."""
        self.__processed_count = 0
        self.__error_count = 0


class BaseParser(BaseProcessor, ParserInterface, ABC):
    """An abstract base class for components that parse data.

    This class extends BaseProcessor with parsing-specific features like
    input validation toggling. It is an abstract class because it does not
    implement the `parse` method from ParserInterface.
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name)
        self.__validation_enabled = True

    @property
    def validation_enabled(self) -> bool:
        """Return True if input validation is currently enabled."""
        return self.__validation_enabled

    def disable_validation(self) -> None:
        """Disable input validation to improve performance."""
        self.__validation_enabled = False

    def enable_validation(self) -> None:
        """Enable input validation."""
        self.__validation_enabled = True

    @abstractmethod
    def parse(self, input_data: Any) -> Any:
        """Parse the input data and return a structured output."""
        raise NotImplementedError

    def validate_input(self, input_data: Any) -> bool:
        """Provide a default input validation implementation.

        Can be overridden by subclasses for more specific validation logic.
        """
        if not self.validation_enabled:
            return True
        return input_data is not None

    def _handle_parsing_error(self, error: Exception, context: str) -> None:
        """A standardized helper method for logging parsing errors."""
        self._increment_errors()
        self._set_status("error")
        print(f"Error in {context}: {error}")
