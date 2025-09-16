"""Validation and report generation with improved OOP design."""

# Standard library imports
import os
from typing import Any, Dict, List

# Third-party imports
import pandas as pd

# Local imports
from base_classes import BaseProcessor
from helpers import JSONLHandler
from interfaces import ValidatorInterface


class MetadataValidator:
    """Specialized validator for metadata."""
    
    def __init__(self):
        self._required_fields = (
            "doc_title", "revision", "version", "release_date"
        )
        self._validation_count = 0
    
    @property
    def required_fields(self) -> tuple:
        """Get required metadata fields."""
        return self._required_fields
    
    @property
    def validation_count(self) -> int:
        """Get number of validations performed."""
        return self._validation_count
    
    def validate(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metadata structure and content."""
        self._validation_count += 1
        
        if not self._is_valid_structure(metadata):
            return self._create_error_result("Metadata is not a dictionary")
        
        errors = self._check_required_fields(metadata)
        return {"is_valid": not errors, "errors": errors}
    
    def _is_valid_structure(self, metadata: Dict[str, Any]) -> bool:
        """Check if metadata has valid structure."""
        return isinstance(metadata, dict)
    
    def _check_required_fields(self, metadata: Dict[str, Any]) -> List[str]:
        """Check for missing required fields."""
        errors = []
        for field in self._required_fields:
            if not metadata.get(field):
                errors.append(f"Missing required field: {field}")
        return errors
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result dictionary."""
        return {"is_valid": False, "errors": [error_message]}


class CoverageCalculator:
    """Calculates various coverage metrics."""
    
    def __init__(self):
        self._calculations_performed = 0
    
    @property
    def calculations_performed(self) -> int:
        """Get number of calculations performed."""
        return self._calculations_performed
    
    def calculate_page_coverage(self, pages_with_text: int, 
                              total_pages: int) -> float:
        """Calculate page coverage percentage."""
        self._calculations_performed += 1
        return self._safe_percentage_calculation(pages_with_text, total_pages)
    
    def calculate_toc_coverage(self, covered_pages: int, 
                             total_pages: int) -> float:
        """Calculate TOC coverage percentage."""
        self._calculations_performed += 1
        return self._safe_percentage_calculation(covered_pages, total_pages)
    
    def calculate_section_coverage(self, sections_count: int, 
                                 pages_with_text: int) -> float:
        """Calculate section coverage percentage."""
        self._calculations_performed += 1
        return self._safe_percentage_calculation(sections_count, 
                                               pages_with_text)
    
    def calculate_toc_pages_covered(self, toc_entries: List[Dict], 
                                  total_pages: int) -> int:
        """Calculate number of pages covered by TOC."""
        valid_entries = self._filter_valid_toc_entries(toc_entries)
        covered_pages = self._calculate_covered_page_set(
            valid_entries, total_pages
        )
        
        self._calculations_performed += 1
        return len(covered_pages)
    
    def _safe_percentage_calculation(self, numerator: int, 
                                   denominator: int) -> float:
        """Safely calculate percentage with zero-division protection."""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator * 100), 2)
    
    def _filter_valid_toc_entries(self, toc_entries: List[Dict]) -> List[Dict]:
        """Filter and sort valid TOC entries."""
        valid_entries = [
            entry for entry in toc_entries
            if isinstance(entry.get("page"), int) and entry["page"] > 0
        ]
        return sorted(valid_entries, key=lambda x: x["page"])
    
    def _calculate_covered_page_set(self, entries: List[Dict], 
                                  total_pages: int) -> set:
        """Calculate set of pages covered by TOC entries."""
        covered_pages = set()
        
        for i, entry in enumerate(entries):
            page_range = self._get_entry_page_range(
                entry, entries, i, total_pages
            )
            covered_pages.update(page_range)
        
        return covered_pages
    
    def _get_entry_page_range(self, entry: Dict, all_entries: List[Dict], 
                            current_index: int, total_pages: int) -> range:
        """Get page range for a single TOC entry."""
        start = int(entry["page"])
        
        if current_index + 1 < len(all_entries):
            end = int(all_entries[current_index + 1]["page"]) - 1
        else:
            end = total_pages
        
        return range(start, max(end, start) + 1)


class Validator(BaseProcessor, ValidatorInterface):
    """Enhanced validator with better encapsulation and single responsibility."""
    
    def __init__(self, **file_paths):
        super().__init__("Validator")
        self._file_paths = self._initialize_file_paths(**file_paths)
        self._output_path = self._file_paths.pop(
            "out_path", "validation_report.xlsx"
        )
        
        # Initialize components
        self._file_handler = JSONLHandler()
        self._metadata_validator = MetadataValidator()
        self._coverage_calculator = CoverageCalculator()
    
    @property
    def output_path(self) -> str:
        """Get output file path."""
        return self._output_path
    
    @output_path.setter
    def output_path(self, value: str) -> None:
        """Set output path with validation."""
        if not self._is_valid_path(value):
            raise ValueError("Invalid output path")
        self._output_path = value
    
    def validate_data(self, data: Any) -> Dict[str, Any]:
        """Validate processed data (implementation of interface method)."""
        return {"is_valid": data is not None, "errors": []}
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        self._set_status("generating")
        
        try:
            summary = self._create_validation_summary()
            self._save_excel_report(summary)
            self._finalize_report_generation(summary)
            
            return summary
            
        except Exception as e:
            self._handle_report_generation_error(e)
            return {}
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Static method for backwards compatibility."""
        validator = MetadataValidator()
        return validator.validate(metadata)
    
    def _initialize_file_paths(self, **kwargs) -> Dict[str, str]:
        """Initialize file paths with defaults."""
        default_paths = {
            "metadata_file": "usb_pd_metadata.jsonl",
            "toc_file": "usb_pd_toc.jsonl",
            "spec_file": "usb_pd_spec.jsonl",
            "pages_file": "usb_pd_pages.jsonl"
        }
        default_paths.update(kwargs)
        return default_paths
    
    def _create_validation_summary(self) -> Dict[str, Any]:
        """Create comprehensive validation summary."""
        file_data = self._load_all_files()
        return self._calculate_comprehensive_metrics(file_data)
    
    def _load_all_files(self) -> Dict[str, List[Dict]]:
        """Load all required data files."""
        file_data = {}
        
        for file_type, file_path in self._file_paths.items():
            file_data[file_type] = self._load_single_file(file_type, file_path)
        
        return file_data
    
    def _load_single_file(self, file_type: str, file_path: str) -> List[Dict]:
        """Load a single data file with error handling."""
        try:
            return list(self._file_handler.read_jsonl(file_path))
        except Exception as e:
            print(f"Warning: Could not load {file_type} from {file_path}: {e}")
            return []
    
    def _calculate_comprehensive_metrics(self, 
                                       file_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Calculate all validation metrics."""
        # Extract data components
        data_components = self._extract_data_components(file_data)
        
        # Calculate basic metrics
        basic_metrics = self._calculate_basic_metrics(data_components)
        
        # Calculate coverage metrics
        coverage_metrics = self._calculate_coverage_metrics(
            data_components, basic_metrics
        )
        
        # Validate metadata
        metadata_status = self._validate_metadata_status(
            data_components["metadata"]
        )
        
        return {
            "Metadata Status": metadata_status,
            **basic_metrics,
            **coverage_metrics
        }
    
    def _extract_data_components(self, 
                               file_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Extract data components from loaded files."""
        return {
            "metadata": file_data.get("metadata_file", []),
            "toc_entries": file_data.get("toc_file", []),
            "sections": file_data.get("spec_file", []),
            "pages": file_data.get("pages_file", [])
        }
    
    def _calculate_basic_metrics(self, 
                               data_components: Dict[str, List[Dict]]) -> Dict[str, int]:
        """Calculate basic counting metrics."""
        pages = data_components["pages"]
        
        return {
            "Total ToC Entries": len(data_components["toc_entries"]),
            "Sections Parsed": len(data_components["sections"]),
            "Pages with Text": sum(
                1 for p in pages if p.get("text", "").strip()
            )
        }
    
    def _calculate_coverage_metrics(self, 
                                  data_components: Dict[str, List[Dict]],
                                  basic_metrics: Dict[str, int]) -> Dict[str, float]:
        """Calculate coverage metrics."""
        pages = data_components["pages"]
        toc_entries = data_components["toc_entries"]
        sections = data_components["sections"]
        
        total_pages = len(pages)
        pages_with_text = basic_metrics["Pages with Text"]
        
        # Calculate TOC pages covered
        toc_pages_covered = self._coverage_calculator.calculate_toc_pages_covered(
            toc_entries, total_pages
        )
        
        return {
            "TOC Covered Pages": toc_pages_covered,
            "Page Coverage (%)": self._coverage_calculator.calculate_page_coverage(
                pages_with_text, total_pages
            ),
            "TOC Coverage (%)": self._coverage_calculator.calculate_toc_coverage(
                toc_pages_covered, total_pages
            ),
            "Section Coverage (%)": self._coverage_calculator.calculate_section_coverage(
                len(sections), pages_with_text
            )
        }
    
    def _validate_metadata_status(self, metadata: List[Dict]) -> str:
        """Validate metadata and return status string."""
        if not metadata:
            return "Missing"
        
        validation_result = self._metadata_validator.validate(metadata[0])
        if validation_result["is_valid"]:
            return "Valid"
        else:
            return "Invalid/Missing"
    
    def _save_excel_report(self, summary: Dict[str, Any]) -> None:
        """Save summary to Excel file."""
        try:
            df = pd.DataFrame([summary])
            df.to_excel(self._output_path, index=False)
        except Exception as e:
            self._handle_excel_save_error(e, summary)
    
    def _handle_excel_save_error(self, error: Exception, 
                               summary: Dict[str, Any]) -> None:
        """Handle Excel save errors with JSON fallback."""
        print(f"Error saving Excel report: {error}")
        # Fallback: save as JSON
        import json
        json_path = self._output_path.replace('.xlsx', '.json')
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Saved as JSON instead: {json_path}")
    
    def _finalize_report_generation(self, summary: Dict[str, Any]) -> None:
        """Finalize report generation process."""
        self._set_status("completed")
        self._increment_processed()
        
        print(f"Validation report generated: {self._output_path}")
        print("Summary:", summary)
    
    def _handle_report_generation_error(self, error: Exception) -> None:
        """Handle report generation errors."""
        self._set_status("error")
        self._increment_errors()
        print(f"Error generating report: {error}")
    
    def _is_valid_path(self, path: str) -> bool:
        """Check if path is valid."""
        return path and isinstance(path, str)


class ReportGenerator:
    """Static factory class for generating validation reports."""
    
    @staticmethod
    def generate_validation_report(toc_file: str, spec_file: str,
                                 pages_file: str = "usb_pd_pages.jsonl",
                                 output_excel: str = "validation_report.xlsx") -> Dict[str, Any]:
        """Generate validation report using provided files."""
        validator = Validator(
            toc_file=toc_file,
            spec_file=spec_file,
            pages_file=pages_file,
            out_path=output_excel
        )
        
        return validator.generate_report()
