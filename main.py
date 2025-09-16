from extractor import PDFExtractor
from helpers import Helper
from metadata_parser import MetadataParser
from section_parser import SectionParser
from toc_parser import TOCParser
from validation_report import ReportGenerator


class PDFPipeline:
    """Pipeline to parse a USB PD PDF and generate outputs."""

    def __init__(self, pdf_file: str):
        """
        Initialize PDFPipeline.

        Args:
            pdf_file (str): Path to the PDF file.
        """
        self._pdf_file = pdf_file

    def run_pipeline(self):
        """Run the full pipeline: metadata, TOC, sections, report."""
        metadata = MetadataParser(self._pdf_file).parse_metadata()
        pdf_extractor = PDFExtractor(self._pdf_file)
        pdf_extractor.dump_all_pages_jsonl("usb_pd_pages.jsonl")

        pages_for_toc = [
            p for p in Helper.read_jsonl("usb_pd_pages.jsonl")
            if p.get("page") and p["page"] <= 60
        ]
        toc_entries = TOCParser(metadata.get("doc_title")).parse_toc(
            pages_for_toc
        )
        Helper.write_jsonl("usb_pd_toc.jsonl", toc_entries)

        SectionParser(
            self._pdf_file, toc_file="usb_pd_toc.jsonl"
        ).parse_sections(toc_entries, out_path="usb_pd_spec.jsonl")

        ReportGenerator.generate_validation_report(
            "usb_pd_toc.jsonl", "usb_pd_spec.jsonl"
        )


if __name__ == "__main__":
    pdf_path = "USB_PD_R3_2 V1.1 2024-10.pdf"
    pipeline = PDFPipeline(pdf_path)
    pipeline.run_pipeline()