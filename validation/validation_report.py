"""Validation and report generation with improved OOP design."""

# Standard library imports
import os
from typing import Any, Dict, List

# Third-party imports
import pandas as pd

# Local imports
from core.base_classes import BaseProcessor
from utils.helpers import JSONLHandler
from core.interfaces import ValidatorInterface
from validation.metadata_validator import MetadataValidator
from validation.coverage_calculator import CoverageCalculator



class Validator(BaseProcessor, 
              ValidatorInterface):
    """Enhanced validator with better encapsulation , single responsibility
    principle."""
    
    def __init__(self, **file_paths: str):
        super().__init__("Validator")
        self.__file_paths = self.__initialize_file_paths(**file_paths)
        self.__output_path = self.__file_paths.pop(
            "out_path", "validation_report.xlsx"
        )
        
        # Composition of helper components
        self.__file_handler = JSONLHandler()
        self.__metadata_validator = MetadataValidator()
        self.__coverage_calculator = CoverageCalculator()

    @property
    def output_path(self) -> str:
        """Return the configured output path for validation report."""
        return self.__output_path

    @output_path.setter
    def output_path(self, value: str) -> None:
        """Set the output file path after validation."""
        if not self.__is_valid_path(value):
            raise ValueError("Output file path must be a non-empty string.")
        self.__output_path = value
    
    def validate_data(self, data: Any) -> Dict[str, Any]:
        """A simple data validation check.

        placeholder implementation as per the interface. The main logic
        is within `generate_report`.
        """
        return {"is_valid": data is not None, "errors": []}

    def generate_report(self) -> Dict[str, Any]:
        """full validation and report generation process."""
        self._set_status("generating")
        try:
            summary = self.__create_validation_summary()
            self.__save_excel_report(summary)
            self.__finalize_report_generation(summary)
            return summary
        except Exception as e:
            self.__handle_report_generation_error(e)
            return {}

    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """for backward compatibility to validate metadata."""
        validator = MetadataValidator()
        return validator.validate(metadata)
    
    def __initialize_file_paths(self, **kwargs: str) -> Dict[str, str]:
        """Initialize the file paths for all required data files."""
        default_paths = {
            "metadata_file": "usb_pd_metadata.jsonl",
            "toc_file": "usb_pd_toc.jsonl",
            "spec_file": "usb_pd_spec.jsonl",
            "pages_file": "usb_pd_pages.jsonl",
        }
        default_paths.update(kwargs)
        return default_paths

    def __create_validation_summary(self) -> Dict[str, Any]:
        """data files and calculate a comprehensive set of metrics."""
        file_data = self.__load_all_files()
        return self.__calculate_comprehensive_metrics(file_data)

    def __load_all_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all required JSONL data files into a dictionary."""
        file_data: Dict[str, List[Dict[str, Any]]] = {}
        for file_type, file_path in self.__file_paths.items():
            file_data[file_type] = (
                self.__load_single_file(file_type, file_path)
            )
        return file_data

    def __load_single_file(
        self, file_type: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """Load a single JSONL file with error handling."""
        try:
            return list(self.__file_handler.read_jsonl(file_path))
        except Exception as e:
            print(f"Warning: Could not load {file_type} from {file_path}: {e}")
            return []
    
    def __calculate_comprehensive_metrics(
        self, file_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Calculate and aggregate all validation metrics."""
        data_components = self.__extract_data_components(file_data)
        basic_metrics = self.__calculate_basic_metrics(data_components)
        coverage_metrics = self.__calculate_coverage_metrics(
            data_components, basic_metrics
        )
        metadata_status = (
            self.__validate_metadata_status(data_components["metadata"])
        )
        
        return {
            "Metadata Status": metadata_status,
            **basic_metrics,
            **coverage_metrics,
        }

    def __extract_data_components(
        self, file_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract and structure data types from the loaded file data."""
        return {
            "metadata": file_data.get("metadata_file", []),
            "toc_entries": file_data.get("toc_file", []),
            "sections": file_data.get("spec_file", []),
            "pages": file_data.get("pages_file", []),
        }

    def __calculate_basic_metrics(
        self, data_components: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, int]:
        """Calculate simple count-based metrics."""
        pages = data_components["pages"]
        return {
            "Total ToC Entries": len(data_components["toc_entries"]),
            "Sections Parsed": len(data_components["sections"]),
            "Pages with Text": sum(
                1 for p in pages if p.get("text", "").strip()
            ),
        }

    def __calculate_coverage_metrics(
        self, data_components: Dict[str, List[Dict[str, Any]]],
        basic_metrics: Dict[str, int]
    ) -> Dict[str, float]:
        """Coordinate the calculation of all coverage-related metrics."""
        pages = data_components["pages"]
        toc_entries = data_components["toc_entries"]
        sections = data_components["sections"]
        
        total_pages = len(pages)
        pages_with_text = basic_metrics["Pages with Text"]
        
        toc_pages_covered = (
            self.__coverage_calculator.calculate_toc_pages_covered(
                toc_entries, total_pages
            )
        )
        
        return {
            "TOC Covered Pages": toc_pages_covered,
            "Page Coverage (%)": (
                self.__coverage_calculator.calculate_page_coverage(
                    pages_with_text, total_pages
                )
            ),
        }

    def __validate_metadata_status(
        self, metadata: List[Dict[str, Any]]
    ) -> str:
        """Validate the metadata and return a simple status string."""
        if not metadata:
            return "Missing"
        
        validation_result = self.__metadata_validator.validate(metadata[0])
        return "Valid" if validation_result["is_valid"] else "Invalid/Missing"
    
    def __save_excel_report(self, summary: Dict[str, Any]) -> None:
        """Save the validation summary to an Excel file."""
        try:
            df = pd.DataFrame([summary])
            df.to_excel(self.__output_path, index=False)
        except Exception as e:
            self.__handle_excel_save_error(e, summary)

    def __handle_excel_save_error(
        self, error: Exception, summary: Dict[str, Any]
    ) -> None:
        """Handle errors Excel report saving by falling back to JSON."""
        print(f"Error saving Excel report: {error}")
        json_path = self.__output_path.replace(".xlsx", ".json")
        try:
            with open(json_path, "w") as f:
                json.dump(summary, f, indent=2)
            print(f"Saved report as JSON instead: {json_path}")
        except Exception as json_e:
            print(f"Failed to save fallback JSON report: {json_e}")

    def __finalize_report_generation(self, summary: Dict[str, Any]) -> None:
        """Finalize the report generation process by updating status."""
        self._set_status("completed")
        self._increment_processed()
        print(f"Validation report generated: {self.__output_path}")

    def __handle_report_generation_error(self, error: Exception) -> None:
        """Log an error that occurs during the report generation process."""
        self._set_status("error")
        self._increment_errors()
        print(f"Error generating report: {error}")

    def __is_valid_path(self, path: str) -> bool:
        """Check if the provided path is a non-empty string."""
        return isinstance(path, str) and bool(path)


class ReportGenerator:
    """A static factory class for generating validation reports.

    Class provides a simplified, single-method entry point for running the
    entire validation process. It is intended for users who do not need to
    customize the `Validator` instance.
    """

    @staticmethod
    def generate_validation_report(
        toc_file: str,
        spec_file: str,
        pages_file: str = "usb_pd_pages.jsonl",
        output_excel: str = "validation_report.xlsx",
    ) -> Dict[str, Any]:
        """Create a `Validator` instance and run the report generation."""
        validator = Validator(
            toc_file=toc_file,
            spec_file=spec_file,
            pages_file=pages_file,
            out_path=output_excel,
        )
        return validator.generate_report()
