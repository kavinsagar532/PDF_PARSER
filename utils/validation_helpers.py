"""Validation helper utilities."""

# Standard library imports
from typing import Any, Dict, List, Optional, Set


class ValidationHelper:
    """Helper class for common validation operations."""
    
    def __init__(self):
        self._validation_cache = {}
    
    def validate_required_fields(self, data: Dict[str, Any], 
                                required_fields: List[str]) -> List[str]:
        """Validate that all required fields are present."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        return missing_fields
    
    def validate_data_types(self, data: Dict[str, Any], 
                           type_specs: Dict[str, type]) -> List[str]:
        """Validate data types of fields."""
        type_errors = []
        for field, expected_type in type_specs.items():
            if field in data and not isinstance(data[field], expected_type):
                type_errors.append(f"{field}: expected {expected_type.__name__}, got {type(data[field]).__name__}")
        return type_errors
    
    def validate_page_range(self, start_page: int, end_page: int, 
                           total_pages: int) -> Optional[str]:
        """Validate page range parameters."""
        if start_page < 1:
            return "Start page must be at least 1"
        if end_page > total_pages:
            return f"End page ({end_page}) exceeds total pages ({total_pages})"
        if start_page > end_page:
            return "Start page cannot be greater than end page"
        return None
    
    def validate_file_exists(self, file_path: str) -> bool:
        """Validate that a file exists."""
        try:
            import os
            return os.path.isfile(file_path)
        except (OSError, TypeError):
            return False
    
    def validate_json_structure(self, data: Any, 
                               required_structure: Dict[str, type]) -> List[str]:
        """Validate JSON data structure."""
        if not isinstance(data, dict):
            return ["Data must be a dictionary"]
        
        errors = []
        for key, expected_type in required_structure.items():
            if key not in data:
                errors.append(f"Missing required key: {key}")
            elif not isinstance(data[key], expected_type):
                errors.append(f"Key '{key}' must be of type {expected_type.__name__}")
        
        return errors
    
    def validate_page_coverage(self, covered_pages: Set[int], 
                              total_pages: int, 
                              minimum_coverage: float = 0.8) -> Dict[str, Any]:
        """Validate page coverage statistics."""
        coverage_ratio = len(covered_pages) / total_pages if total_pages > 0 else 0
        
        return {
            "covered_pages": len(covered_pages),
            "total_pages": total_pages,
            "coverage_ratio": coverage_ratio,
            "meets_minimum": coverage_ratio >= minimum_coverage,
            "uncovered_pages": set(range(1, total_pages + 1)) - covered_pages
        }
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters."""
        import re
        # Remove or replace invalid filename characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        return sanitized if sanitized else "untitled"
    
    def validate_toc_entry(self, entry: Dict[str, Any]) -> List[str]:
        """Validate a table of contents entry."""
        errors = []
        
        required_fields = ["section_id", "title", "page"]
        missing = self.validate_required_fields(entry, required_fields)
        errors.extend(missing)
        
        # Validate specific field types
        if "page" in entry and not isinstance(entry["page"], int):
            errors.append("Page number must be an integer")
        
        if "page" in entry and entry["page"] < 1:
            errors.append("Page number must be positive")
        
        if "title" in entry and not entry["title"].strip():
            errors.append("Title cannot be empty")
        
        return errors