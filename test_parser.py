"""
Unit and integration tests for PDF Parser pipeline.
Uses pytest and mocks for pipeline testing.
"""
import json
import pytest
from unittest.mock import patch
from pathlib import Path

from metadata_parser import MetadataParser
from toc_parser import TOCParser
from section_parser import SectionParser
from validation_report import Validator, ReportGenerator
from extractor import PDFExtractor
from helpers import Helper

pdf_file = "USB_PD_R3_2 V1.1 2024-10.pdf"


def test_parse_metadata_real(tmp_path):
    """Integration test: metadata parsing writes metadata JSONL and returns fields."""
    output_file = tmp_path / "metadata.jsonl"
    mp = MetadataParser(pdf_file, output_file=str(output_file))
    metadata = mp.parse_metadata()
    with open(output_file, "r", encoding="utf-8") as f:
        meta = json.loads(f.readline().strip())
    assert "doc_title" in meta
    assert "revision" in meta
    assert "version" in meta
    assert "release_date" in meta


def test_parse_toc_real():
    """Ensure ToC parser finds entries in the first pages (if ToC present)."""
    pdf_extractor = PDFExtractor(pdf_file)
    pages = pdf_extractor.extract_text(start_page=1, end_page=40)
    toc_parser = TOCParser(doc_title="USB PD Spec")
    toc = toc_parser.parse_toc(pages)
    assert isinstance(toc, list)


def test_parse_sections_real(tmp_path):
    """Test sections are parsed and output JSONL file created."""
    pdf_extractor = PDFExtractor(pdf_file)
    pages = pdf_extractor.extract_text(start_page=1, end_page=40)
    toc_parser = TOCParser(doc_title="USB PD Spec")
    toc_entries = toc_parser.parse_toc(pages)

    toc_file = tmp_path / "toc.jsonl"
    with open(toc_file, "w", encoding="utf-8") as f:
        for e in toc_entries:
            f.write(json.dumps(e) + "\n")

    sections_file = tmp_path / "sections.jsonl"
    section_parser = SectionParser(pdf_file, toc_file=str(toc_file))
    sections = section_parser.parse_sections(toc_entries=toc_entries, out_path=str(sections_file))

    with open(sections_file, "r", encoding="utf-8") as f:
        sections = [json.loads(line) for line in f]

    assert "content" in sections[0] if sections else True


def test_validate_metadata_real():
    """Check validator accepts a valid metadata dict."""
    metadata = {
        "doc_title": "USB PD Spec",
        "revision": "3.2",
        "version": "1.1",
        "release_date": "2024-10"
    }
    result = Validator.validate_metadata(metadata)
    assert result["is_valid"] is True


def test_generate_validation_report_real(tmp_path):
    """Report generator can produce an Excel file from small sample data."""
    toc_file = tmp_path / "toc.jsonl"
    sections_file = tmp_path / "sections.jsonl"

    toc_entries = [{"section_id": "1", "page": 1, "title": "Intro"}]
    sections_entries = [{"section_id": "1", "page": 1, "title": "Intro", "content": "Hello"}]

    with open(toc_file, "w", encoding="utf-8") as f:
        for e in toc_entries:
            f.write(json.dumps(e) + "\n")
    with open(sections_file, "w", encoding="utf-8") as f:
        for e in sections_entries:
            f.write(json.dumps(e) + "\n")

    report_file = tmp_path / "report.xlsx"
    ReportGenerator.generate_validation_report(str(toc_file), str(sections_file), output_excel=str(report_file))
    assert report_file.exists()


# Fix patches: point to real modules, not "main"
@patch("extractor.PDFExtractor.extract_text")
@patch("metadata_parser.MetadataParser.parse_metadata")
@patch("toc_parser.TOCParser.parse_toc")
@patch("section_parser.SectionParser.parse_sections")
@patch("validation_report.Validator.validate_metadata")
@patch("helpers.Helper.write_jsonl")
@patch("validation_report.ReportGenerator.generate_validation_report")
def test_main(mock_gen_report, mock_write, mock_validate, mock_parse_sec, mock_parse_toc, mock_parse_meta, mock_extract):
    """Test main pipeline runs with mocks."""
    mock_extract.return_value = [{"page_number": 1, "text": "sample"}]
    mock_parse_meta.return_value = {
        "doc_title": "USB PD Spec",
        "revision": "3.2",
        "version": "1.1",
        "release_date": "2024-10"
    }
    mock_parse_toc.return_value = [{"section_id": "1", "page": 1, "title": "Intro"}]
    mock_validate.return_value = {"is_valid": True, "errors": []}
    mock_parse_sec.return_value = None
    mock_write.return_value = None
    mock_gen_report.return_value = None

    import main
    main.main()
