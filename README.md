# PDF Parser

# Overview
This project is a Python-based PDF parser designed to extract information from PDFs.
It automates the extraction of metadata, Table of Contents (ToC), and section contents,
and generates validation reports to ensure data accuracy and completeness.

# Features
- Metadata Extraction: Extracts document title, revision, version, and release date.
- Table of Contents Parsing: Detects section hierarchy from the ToC.
- Section Extraction: Collects full content of each section
- Validation: Checks for missing or extra sections and validates metadata formats.
- Reports: Generates Excel validation reports summarizing completeness.
- Unit Testing: Comprehensive tests using pytest with coverage support.

# Project Structure
- extractor.py – Extracts text from PDF pages using pdfplumber.  
- helpers.py – Helper functions, such as writing JSONL files.  
- metadata_parser.py – Extracts metadata from the PDF.  
- toc_parser.py – Parses the Table of Contents from extracted pages.  
- section_parser.py – Extracts sections.  
- validation_report.py – Validates metadata and generates reports.  
- main.py – Runs the full PDF parsing pipeline.  
- test_parser.py – Pytest unit tests for all modules and main.py.  
- USB_PD_R3_2 V1.1 2024-10.pdf – Sample PDF file.  
- .gitignore – Ignores virtual environment and unnecessary files.  

# Run the Project
- python main.py

# Generated Files
- Metadata: usb_pd_metadata.jsonl  
- Table of Contents: usb_pd_toc.jsonl
- Sections: usb_pd_spec.jsonl
- Validation Report: validation_report.xlsx

# Author
Kavin Sagar R
