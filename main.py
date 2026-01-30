"""The main entry point and pipeline for the PDF parsing application.

This module defines the `PDFPipeline` class, which coordinates the entire
workflow from text extraction to validation report generation. It also
contains the `main` function to execute the pipeline from the command line.
"""

# Standard library imports
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

# Local imports
from core.base_classes import BaseProcessor
from parsers.extractor import PDFExtractor
from utils.helpers import JSONLHandler
from core.interfaces import PipelineInterface
from parsers.metadata_parser import MetadataParser
from parsers.section_parser import SectionParser
from parsers.toc_parser import TOCParser
from validation.validation_report import ReportGenerator
from validation.coverage_calculator import CoverageCalculator


class PDFPipeline(BaseProcessor, PipelineInterface):
    """An orchestrator for the entire PDF processing workflow.

    composes all the necessary parser and processor components and
    executes them in a predefined sequence. All internal state and helper
    methods are private to ensure a clean public API.
    """

    def __init__(self, pdf_file: str):
        super().__init__("PDFPipeline")
        self.__pdf_file = pdf_file
        self.__results: Dict[str, Any] = {}
        self.__current_step = 0

        # Centralized file path configuration
        self.__file_paths = {
            "metadata": "usb_pd_metadata.jsonl",
            "pages": "usb_pd_pages.jsonl",
            "toc": "usb_pd_toc.jsonl",
            "spec": "usb_pd_spec.jsonl",
            "report": "validation_report.xlsx",
        }

        # Component initialization (Dependency Injection)
        self.__file_handler = JSONLHandler()
        self.__extractor = PDFExtractor(self.__pdf_file)
        self.__metadata_parser = MetadataParser(
            self.__pdf_file, self.__file_paths["metadata"]
        )
        self.__toc_parser = TOCParser()
        self.__section_parser = SectionParser(
            pdf_path=self.__pdf_file,
            toc_file=self.__file_paths["toc"],
            pages_file=self.__file_paths["pages"],
        )
        self.__coverage_calculator = CoverageCalculator()

        # The sequence of pipeline steps
        self.__pipeline_steps: List[
            Tuple[str, Callable[[], Any]]
        ] = self.__initialize_pipeline_steps()

    @property
    def pipeline_status(self) -> Dict[str, Any]:
        """Return a dictionary with the current status of the pipeline."""
        return {
            "current_step": self.__current_step,
            "total_steps": len(self.__pipeline_steps),
            "status": self.status,
            "results_available": bool(self.__results),
        }

    @property
    def results(self) -> Dict[str, Any]:
        """Return a copy of the pipeline's execution results."""
        return self.__results.copy()

    def run_pipeline(self) -> None:
        """complete PDF processing pipeline from start to finish."""
        self._set_status("running")
        try:
            print(f"Processing: {self.__pdf_file}")
            self.__execute_pipeline_steps()
            self.__finalize_pipeline()
        except Exception as e:
            self.__handle_pipeline_error(e)
            raise

    def __initialize_pipeline_steps(
        self
    ) -> List[Tuple[str, Callable[[], Any]]]:
        """Define the sequence of steps to be executed in the pipeline."""
        return [
            ("PDF Text Extraction", self.__extract_pdf_text),
            ("Metadata Extraction", self.__extract_metadata),
            ("TOC Parsing", self.__parse_toc),
            ("Section Parsing", self.__parse_sections),
            ("Validation Report", self.__generate_validation_report),
        ]

    def __execute_pipeline_steps(self) -> None:
        """Execute all defined pipeline steps in sequence."""
        for step_name, step_function in self.__pipeline_steps:
            self.__execute_single_step(step_name, step_function)

    def __execute_single_step(
        self, step_name: str, step_function: Callable[[], Any]
    ) -> None:
        """Execute a single step of the pipeline and store its result."""
        print(f"Step {self.__current_step + 1}/5: {step_name}")
        result = step_function()
        self.__results[step_name] = result
        self.__current_step += 1

    def __extract_pdf_text(self) -> Optional[int]:
        """Step 1: Extract text from all pages of the PDF."""
        try:
            return self.__extractor.dump_all_pages_jsonl(
                self.__file_paths["pages"]
            )
        except Exception as e:
            print(f"PDF text extraction failed: {e}")
            return None

    def __extract_metadata(self) -> Optional[Dict[str, Any]]:
        """Step 2: Extract document metadata."""
        try:
            return self.__metadata_parser.parse_metadata()
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return None

    def __parse_toc(self) -> Optional[List[Dict[str, Any]]]:
        """Step 3: Parse the Table of Contents."""
        try:
            pages_for_toc = self.__load_toc_pages()
            self.__toc_parser.doc_title = self.__get_document_title()
            toc_entries = self.__toc_parser.parse_toc(pages_for_toc)
            self.__file_handler.write_jsonl(
                self.__file_paths["toc"], toc_entries
            )
            
            return toc_entries
        except Exception as e:
            print(f"TOC parsing failed: {e}")
            return None

    def __parse_sections(self) -> Optional[List[Dict[str, Any]]]:
        """Step 4: Parse the main document sections with enhancement."""
        try:
            toc_entries = self.__results.get("TOC Parsing", [])
            # Ensure toc_entries is a list, not None
            if toc_entries is None:
                toc_entries = []
                print(
                    "Warning: TOC parsing returned None, using empty list "
                    "for section parsing"
                )
            
            sections = self.__section_parser.parse_sections(
                toc_entries, self.__file_paths["spec"]
            )
            
            return sections
        except Exception as e:
            print(f"Section parsing failed: {e}")
            return None

    def __generate_validation_report(self) -> Optional[Dict[str, Any]]:
        """Step 5: Generate the enhanced validation report with
        comprehensive coverage metrics."""
        try:
            # Generate traditional report
            report = ReportGenerator.generate_validation_report(
                toc_file=self.__file_paths["toc"],
                spec_file=self.__file_paths["spec"],
                pages_file=self.__file_paths["pages"],
                output_excel=self.__file_paths["report"],
            )
            
            # Add enhanced coverage analysis
            enhanced_report = self.__generate_enhanced_coverage_report()
            if enhanced_report:
                report.update(enhanced_report)
            
            return report
        except Exception as e:
            print(f"Validation report generation failed: {e}")
            return None

    def __load_toc_pages(self) -> List[Dict[str, Any]]:
        """Load the first 60 pages, which typically contain the TOC."""
        return [
            page
            for page in self.__file_handler.read_jsonl(
                self.__file_paths["pages"]
            )
            if page.get("page", 0) <= 60
        ]

    def __get_document_title(self) -> str:
        """document title from the parsed metadata, with a fallback."""
        metadata = self.__results.get("Metadata Extraction", {})
        return metadata.get(
            "doc_title",
            "Universal Serial Bus Power Delivery Specification"
        )

    def __finalize_pipeline(self) -> None:
        """Finalize pipeline with clean summary reporting."""
        self._set_status("completed")
        self._increment_processed()
        
        # Print clean completion summary
        print("\nPDF PROCESSING COMPLETED")
        print("-" * 40)
        
        # Print only essential counts
        self.__print_clean_summary()
        
        print("-" * 40)

    def __handle_pipeline_error(self, error: Exception) -> None:
        """Handle any error that causes the pipeline to fail."""
        self._set_status("error")
        self._increment_errors()
        print(
            f"Pipeline failed at step {self.__current_step + 1}: {error}"
        )
    
    def __generate_enhanced_coverage_report(self) -> Optional[Dict[str, Any]]:
        """Generate enhanced coverage metrics using the new analyzers."""
        try:
            # Load extracted pages data
            pages_data = list(
                self.__file_handler.read_jsonl(self.__file_paths["pages"])
            )
            if not pages_data:
                return None
            
            total_pages = len(pages_data)
            
            # Calculate comprehensive coverage
            comprehensive_coverage = (
                self.__coverage_calculator.calculate_comprehensive_coverage(
                    pages_data, total_pages
                )
            )
            
            # Calculate content quality metrics  
            quality_metrics = (
                self.__coverage_calculator.calculate_content_quality_score(
                    pages_data
                )
            )
            
            enhanced_report = {
                'enhanced_coverage_metrics': comprehensive_coverage,
                'content_quality_metrics': quality_metrics,
            }
            
            return enhanced_report
            
        except Exception as e:
            return None
    
    def __print_clean_summary(self) -> None:
        """Print a clean, essential summary."""
        try:
            def count_jsonl_records(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        return sum(1 for line in f if line.strip())
                except Exception:
                    return 0
            
            toc_count = count_jsonl_records(self.__file_paths["toc"])
            spec_count = count_jsonl_records(self.__file_paths["spec"])
            pages_count = count_jsonl_records(self.__file_paths["pages"])
            
            print(f"\nFINAL RESULTS:")
            print(f"  TOC Parsing: {toc_count}")
            print(f"  Section Parsing: {spec_count}")
            print(f"  PDF Text Extraction: {pages_count}")
                    
        except Exception as e:
            print(f"Error printing summary: {e}")
    


def main() -> None:
    """Enhanced main entry point with clean output."""
    try:
        pdf_path = "USB_PD_R3_2 V1.1 2024-10.pdf"
        print("Enhanced PDF Processing Pipeline")
        
        pipeline = PDFPipeline(pdf_path)
        pipeline.run_pipeline()
        
    except KeyboardInterrupt:
        print("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Pipeline failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
