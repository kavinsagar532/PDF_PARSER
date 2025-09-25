"""A module for validating the structure and content of document metadata.

This module provides the `MetadataValidator` class, a specialized component
for checking if a metadata dictionary contains all the required fields.
"""

# Standard library imports
from typing import Any, Dict, List, Tuple


class MetadataValidator:
    """Validates document metadata with a focus on required fields.

    This class encapsulates the logic for checking metadata dictionaries.
    All internal attributes and helper methods are private to ensure clean
    and stable public API.
    """

    def __init__(self):
        self.__required_fields: Tuple[str, ...] = (
            "doc_title", "revision", "version", "release_date"
        )
        self.__validation_count = 0

    @property
    def required_fields(self) -> Tuple[str, ...]:
        """Return the tuple of required metadata field names."""
        return self.__required_fields

    @property
    def validation_count(self) -> int:
        """Return the number of times the validation method has called."""
        return self.__validation_count

    def validate(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the structure and content of a metadata dictionary."""
        self.__validation_count += 1

        if not self.__is_valid_structure(metadata):
            return self.__create_error_result("Metadata must be dictionary.")

        errors = self.__check_required_fields(metadata)
        return {"is_valid": not errors, "errors": errors}

    def __is_valid_structure(self, metadata: Dict[str, Any]) -> bool:
        """Check if the provided metadata is a dictionary."""
        return isinstance(metadata, dict)

    def __check_required_fields(self, metadata: Dict[str, Any]) -> List[str]:
        """Check for the presence of all required fields in the metadata."""
        return [
            f"Missing required field: {field}"
            for field in self.__required_fields
            if not metadata.get(field)
        ]

    def __create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized dictionary for a validation error."""
        return {"is_valid": False, "errors": [error_message]}
