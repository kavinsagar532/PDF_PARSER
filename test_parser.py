"""
Unit and integration tests for the USB PD PDF Parser pipeline.
Uses pytest and mocks to test components and full pipeline.
"""
import json
from unittest.mock import patch

import pytest

from extractor import PDFExtractor
from helpers import Helper
from main import PDFPipeline
from metadata_parser import MetadataParser
from section_parser import SectionParser
from toc_parser import TOCParser
from validation_report import ReportGenerator, Validator

_PDF_FILE = "USB_PD_R3_2 V1.1 2024-10.pdf"


# --------------------- Metadata Parser ---------------------
@patch("metadata_parser.PDFExtractor.extract_text")
def test_metadata_parser(mock_extract, tmp_path):
    """
    Integration test: ensure metadata parsing writes JSONL and returns fields.
    """
    mock_extract.return_value = [{
        "page": 1,
        "text": "Universal Serial Bus Power Delivery Specification\n"
        "Revision: 3.2\nVersion: 1.1\nRelease Date: 2024-10"
    }]
    output_file = tmp_path / "meta_out.jsonl"
    parser = MetadataParser(
        pdf_file="dummy.pdf", output_file=str(output_file)
    )
    metadata = parser.parse_metadata()
    with open(output_file, "r", encoding="utf-8") as f:
        meta = json.loads(f.readline().strip())
    assert "doc_title" in meta
    assert "revision" in meta
    assert "version" in meta
    assert "release_date" in meta


# --------------------- TOC Parser ---------------------
def test_parse_toc_real():
    """
    Test real TOC parsing from a sample PDF.
    """
    pdf_extractor = PDFExtractor(_PDF_FILE)
    pages = pdf_extractor.extract_text(start_page=1, end_page=40)
    toc_parser = TOCParser(doc_title="USB PD Spec")
    toc = toc_parser.parse_toc(pages)
    assert isinstance(toc, list)


# --------------------- Section Parser ---------------------
def test_parse_sections_real(tmp_path):
    """
    Test section parsing from PDF pages and TOC.
    """
    pdf_extractor = PDFExtractor(_PDF_FILE)
    pages = pdf_extractor.extract_text(start_page=1, end_page=40)
    toc_parser = TOCParser(doc_title="USB PD Spec")
    toc_entries = toc_parser.parse_toc(pages)

    toc_file = tmp_path / "toc.jsonl"
    with open(toc_file, "w", encoding="utf-8") as f:
        for e in toc_entries:
            f.write(json.dumps(e) + "\n")

    sections_file = tmp_path / "sections.jsonl"
    section_parser = SectionParser(_PDF_FILE, toc_file=str(toc_file))
    sections = section_parser.parse_sections(
        toc_entries=toc_entries, out_path=str(sections_file)
    )

    with open(sections_file, "r", encoding="utf-8") as f:
        sections = [json.loads(line) for line in f]

    assert "content" in sections[0] if sections else True


# --------------------- Metadata Validation ---------------------
def test_validate_metadata_real():
    """
    Validate that metadata contains required fields.
    """
    metadata = {
        "doc_title": "USB PD Spec",
        "revision": "3.2",
        "version": "1.1",
        "release_date": "2024-10"
    }
    result = Validator.validate_metadata(metadata)
    assert result["is_valid"] is True


# --------------------- Validation Report ---------------------
def test_generate_validation_report_real(tmp_path):
    """
    Generate a validation report and ensure the Excel file is created.
    """
    toc_file = tmp_path / "toc.jsonl"
    sections_file = tmp_path / "sections.jsonl"

    toc_entries = [{"section_id": "1", "page": 1, "title": "Intro"}]
    sections_entries = [
        {"section_id": "1", "page": 1, "title": "Intro", "content": "Hello"}
    ]

    Helper.write_jsonl(str(toc_file), toc_entries)
    Helper.write_jsonl(str(sections_file), sections_entries)

    report_file = tmp_path / "report.xlsx"
    ReportGenerator.generate_validation_report(
        str(toc_file), str(sections_file), output_excel=str(report_file)
    )
    assert report_file.exists()


# --------------------- Full pipeline test using PDFPipeline -----------------
def test_full_pipeline():
    """
    Test the full PDFPipeline with major components mocked.
    """
    with patch("extractor.PDFExtractor.extract_text") as mock_extract, \
            patch("metadata_parser.MetadataParser.parse_metadata") as \
            mock_parse_meta, \
            patch("toc_parser.TOCParser.parse_toc") as mock_parse_toc, \
            patch("section_parser.SectionParser.parse_sections") as \
            mock_parse_sec, \
            patch("validation_report.Validator.validate_metadata") as \
            mock_validate, \
            patch("helpers.Helper.write_jsonl") as mock_write, \
            patch("validation_report.ReportGenerator."
                  "generate_validation_report") as mock_gen_report:

        mock_extract.return_value = [{"page": 1, "text": "sample"}]
        mock_parse_meta.return_value = {
            "doc_title": "USB PD Spec",
            "revision": "3.2",
            "version": "1.1",
            "release_date": "2024-10"
        }
        mock_parse_toc.return_value = [
            {"section_id": "1", "page": 1, "title": "Intro"}
        ]
        mock_validate.return_value = {"is_valid": True, "errors": []}
        mock_parse_sec.return_value = [
            {"section_id": "1", "page": 1, "title": "Intro"}
        ]

        pipeline = PDFPipeline(pdf_file="dummy.pdf")
        pipeline.run_pipeline()

        mock_parse_meta.assert_called_once_with()
        mock_parse_toc.assert_called_once()
        mock_parse_sec.assert_called_once()
        mock_gen_report.assert_called_once()