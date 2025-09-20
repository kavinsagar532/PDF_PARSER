"""
PDF Parser Package

A comprehensive PDF parsing library for extracting metadata, table of contents,
and section content from PDF documents with validation capabilities.

Modules:
    - extractor: PDF text extraction utilities
    - metadata_parser: Document metadata extraction
    - toc_parser: Table of contents parsing
    - section_parser: Document section extraction
    - validation_report: Data validation and reporting
    - helpers: Utility functions and file handlers (compatibility)
    - text_utils: Text processing utilities (compatibility)
    - utils: Modular utility package with improved organization
    - interfaces: Type interfaces and protocols
    - base_classes: Base classes for common functionality
"""

__version__ = "1.0.0"
__author__ = "Kavin Sagar R"

# Core components
from .extractor import PDFExtractor
from .metadata_parser import MetadataParser
from .toc_parser import TOCParser
from .section_parser import SectionParser
from .validation_report import ReportGenerator

# Utilities (backward compatibility)
from .helpers import JSONLHandler, Helper
from .text_utils import TextProcessor

# Modern modular utilities
from .utils import JSONLHandler as ModernJSONLHandler
from .utils import TextProcessor as ModernTextProcessor
from .utils import ValidationHelper

# Interfaces and base classes
from .interfaces import (
    ExtractorInterface,
    ParserInterface,
    PipelineInterface,
    ReportInterface
)
from .base_classes import BaseProcessor

__all__ = [
    "PDFExtractor",
    "MetadataParser", 
    "TOCParser",
    "SectionParser",
    "ReportGenerator",
    "JSONLHandler",
    "Helper",
    "TextProcessor",
    "ModernJSONLHandler",
    "ModernTextProcessor",
    "ValidationHelper",
    "ExtractorInterface",
    "ParserInterface", 
    "PipelineInterface",
    "ReportInterface",
    "BaseProcessor"
]