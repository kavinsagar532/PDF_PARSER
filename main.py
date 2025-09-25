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
            print(f"Starting PDF processing pipeline for:{self.__pdf_file}")
            self.__execute_pipeline_steps()
            self.__finalize_pipeline()
        except Exception as e:
            self.__handle_pipeline_error(e)
            raise

    def __initialize_pipeline_steps(self) -> List[Tuple[str, Callable[[], Any]]]:
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
        print(
            f"Executing step {self.__current_step + 1}/"
            f"{len(self.__pipeline_steps)}: {step_name}"
        )
        result = step_function()
        self.__results[step_name] = result
        self.__current_step += 1
        if result is None:
            print(f"Warning: Step '{step_name}' returned no result.")

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
        """Step 4: Parse the main document sections."""
        try:
            toc_entries = self.__results.get("TOC Parsing", [])
            return self.__section_parser.parse_sections(
                toc_entries, self.__file_paths["spec"]
            )
        except Exception as e:
            print(f"Section parsing failed: {e}")
            return None

    def __generate_validation_report(self) -> Optional[Dict[str, Any]]:
        """Step 5: Generate the final validation report."""
        try:
            return ReportGenerator.generate_validation_report(
                toc_file=self.__file_paths["toc"],
                spec_file=self.__file_paths["spec"],
                pages_file=self.__file_paths["pages"],
                output_excel=self.__file_paths["report"],
            )
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
        """updating its status ,printing a success message."""
        self._set_status("completed")
        self._increment_processed()
        print("Pipeline completed successfully!")

    def __handle_pipeline_error(self, error: Exception) -> None:
        """Handle any error that causes the pipeline to fail."""
        self._set_status("error")
        self._increment_errors()
        print(
            f"Pipeline failed at step {self.__current_step + 1}: {error}"
        )


def main() -> None:
    """Main entry point for the application."""
    try:
        pdf_path = "USB_PD_R3_2 V1.1 2024-10.pdf"
        pipeline = PDFPipeline(pdf_path)
        pipeline.run_pipeline()
        
        # Print final status
        status = pipeline.pipeline_status
        print(f"\nPipeline Status: {status}")
        
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nPipeline failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
