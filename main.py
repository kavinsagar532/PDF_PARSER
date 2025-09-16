"""Enhanced main pipeline with better organization and error handling."""

# Standard library imports
import sys
from typing import Any, Dict, List, Optional

# Local imports
from base_classes import BaseProcessor
from extractor import PDFExtractor
from helpers import JSONLHandler
from interfaces import PipelineInterface
from metadata_parser import MetadataParser
from section_parser import SectionParser
from toc_parser import TOCParser
from validation_report import ReportGenerator


class PDFPipeline(BaseProcessor, PipelineInterface):
    """Enhanced PDF processing pipeline with better OOP design."""
    
    def __init__(self, pdf_file: str):
        super().__init__("PDFPipeline")
        self._pdf_file = pdf_file
        self._pipeline_steps = []
        self._current_step = 0
        self._results = {}
        
        # Initialize file handler
        self._file_handler = JSONLHandler()
        
        # Initialize pipeline steps
        self._initialize_pipeline_steps()
    
    @property
    def pdf_file(self) -> str:
        """Get PDF file path."""
        return self._pdf_file
    
    @property
    def pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status."""
        return {
            "current_step": self._current_step,
            "total_steps": len(self._pipeline_steps),
            "completed_steps": self._current_step,
            "status": self.status,
            "results_available": bool(self._results)
        }
    
    @property
    def results(self) -> Dict[str, Any]:
        """Get pipeline execution results."""
        return self._results.copy()
    
    def run_pipeline(self) -> None:
        """Execute the complete PDF processing pipeline."""
        self._set_status("running")
        
        try:
            print(f"Starting PDF processing pipeline for: {self._pdf_file}")
            
            self._execute_pipeline_steps()
            self._finalize_pipeline()
            
        except Exception as e:
            self._handle_pipeline_error(e)
            raise
    
    def _initialize_pipeline_steps(self) -> None:
        """Initialize the sequence of pipeline steps."""
        self._pipeline_steps = [
            ("metadata_extraction", self._extract_metadata),
            ("pdf_text_extraction", self._extract_pdf_text),
            ("toc_parsing", self._parse_toc),
            ("section_parsing", self._parse_sections),
            ("validation_report", self._generate_validation_report)
        ]
    
    def _execute_pipeline_steps(self) -> None:
        """Execute all pipeline steps in sequence."""
        for step_name, step_function in self._pipeline_steps:
            self._execute_single_step(step_name, step_function)
    
    def _execute_single_step(self, step_name: str, step_function) -> None:
        """Execute a single pipeline step."""
        print(f"Executing step {self._current_step + 1}/"
              f"{len(self._pipeline_steps)}: {step_name}")
        
        result = step_function()
        self._results[step_name] = result
        self._current_step += 1
        
        if result is None:
            print(f"Warning: Step '{step_name}' returned no result")
    
    def _extract_metadata(self) -> Optional[Dict[str, Any]]:
        """Step 1: Extract document metadata."""
        try:
            parser = MetadataParser(self._pdf_file, "usb_pd_metadata.jsonl")
            return parser.parse_metadata()
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return None
    
    def _extract_pdf_text(self) -> Optional[int]:
        """Step 2: Extract text from all PDF pages."""
        try:
            extractor = PDFExtractor(self._pdf_file)
            return extractor.dump_all_pages_jsonl("usb_pd_pages.jsonl")
        except Exception as e:
            print(f"PDF text extraction failed: {e}")
            return None
    
    def _parse_toc(self) -> Optional[List[Dict]]:
        """Step 3: Parse table of contents."""
        try:
            pages_for_toc = self._load_toc_pages()
            doc_title = self._get_document_title()
            
            parser = TOCParser(doc_title)
            toc_entries = parser.parse_toc(pages_for_toc)
            
            # Save TOC entries
            self._file_handler.write_jsonl("usb_pd_toc.jsonl", toc_entries)
            
            return toc_entries
        except Exception as e:
            print(f"TOC parsing failed: {e}")
            return None
    
    def _parse_sections(self) -> Optional[List[Dict]]:
        """Step 4: Parse document sections."""
        try:
            toc_entries = self._results.get("toc_parsing", [])
            
            parser = SectionParser(
                pdf_path=self._pdf_file,
                toc_file="usb_pd_toc.jsonl",
                pages_file="usb_pd_pages.jsonl"
            )
            
            return parser.parse_sections(toc_entries, "usb_pd_spec.jsonl")
        except Exception as e:
            print(f"Section parsing failed: {e}")
            return None
    
    def _generate_validation_report(self) -> Optional[Dict[str, Any]]:
        """Step 5: Generate validation report."""
        try:
            return ReportGenerator.generate_validation_report(
                "usb_pd_toc.jsonl", 
                "usb_pd_spec.jsonl",
                "usb_pd_pages.jsonl",
                "validation_report.xlsx"
            )
        except Exception as e:
            print(f"Validation report generation failed: {e}")
            return None
    
    def _load_toc_pages(self) -> List[Dict]:
        """Load pages for TOC parsing (first 60 pages)."""
        return [
            page for page in self._file_handler.read_jsonl("usb_pd_pages.jsonl")
            if page.get("page", 0) <= 60
        ]
    
    def _get_document_title(self) -> str:
        """Get document title from metadata or use default."""
        metadata = self._results.get("metadata_extraction", {})
        return (metadata.get("doc_title") or 
                "Universal Serial Bus Power Delivery Specification")
    
    def _finalize_pipeline(self) -> None:
        """Finalize pipeline execution."""
        self._set_status("completed")
        self._increment_processed()
        print("Pipeline completed successfully!")
    
    def _handle_pipeline_error(self, error: Exception) -> None:
        """Handle pipeline execution errors."""
        self._set_status("error")
        self._increment_errors()
        print(f"Pipeline failed at step {self._current_step + 1}: {error}")


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
