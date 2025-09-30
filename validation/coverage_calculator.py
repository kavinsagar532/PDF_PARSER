"""A module for calculating various coverage metrics for the parsed data.

This module provides `CoverageCalculator` class, a component specialized
in calculating like page coverage, TOC coverage, and section coverage.
"""

# Standard library imports
from typing import Any, Dict, List, Set


class CoverageCalculator:
    """Calculates various coverage metrics with a focus on encapsulation.

    provides a suite of methods for calculating different coverage
    percentages. All internal state helper methods are private to ensure a
    clean and stable public API.
    """

    def __init__(self):
        self.__calculations_performed = 0

    @property
    def calculations_performed(self) -> int:
        """Return total number of calculations made by this instance."""
        return self.__calculations_performed

    def calculate_page_coverage(
        self, pages_with_text: int, total_pages: int
    ) -> float:
        """Calculate the percentage of pages that contain text."""
        self.__calculations_performed += 1
        return self.__safe_percentage_calculation(pages_with_text, total_pages)
    
    def calculate_comprehensive_coverage(
        self, pages_data: List[Dict[str, Any]], total_pages: int
    ) -> Dict[str, float]:
        """Calculate comprehensive coverage metrics including tables, 
        images, etc."""
        self.__calculations_performed += 1
        
        metrics = {
            'text_coverage': 0.0,
            'table_coverage': 0.0,
            'image_coverage': 0.0,
            'annotation_coverage': 0.0,
            'layout_coverage': 0.0,
            'overall_coverage': 0.0
        }
        
        if not pages_data or total_pages == 0:
            return metrics
        
        pages_with_text = 0
        pages_with_tables = 0
        pages_with_images = 0
        pages_with_annotations = 0
        pages_with_layout = 0
        
        for page in pages_data:
            # Text coverage
            if page.get('text', '').strip():
                pages_with_text += 1
            
            # Table coverage
            if page.get('tables') and len(page['tables']) > 0:
                pages_with_tables += 1
            
            # Image coverage
            if page.get('images') and len(page['images']) > 0:
                pages_with_images += 1
            
            # Annotation coverage
            metadata = page.get('metadata', {})
            annotations = metadata.get('annotations')
            if annotations and len(annotations) > 0:
                pages_with_annotations += 1
            
            # Layout coverage
            layout = page.get('layout', {})
            if layout.get('text_lines') and len(layout['text_lines']) > 0:
                pages_with_layout += 1
        
        # Calculate percentages
        metrics['text_coverage'] = self.__safe_percentage_calculation(
            pages_with_text, total_pages
        )
        metrics['table_coverage'] = self.__safe_percentage_calculation(
            pages_with_tables, total_pages
        )
        metrics['image_coverage'] = self.__safe_percentage_calculation(
            pages_with_images, total_pages
        )
        metrics['annotation_coverage'] = (
            self.__safe_percentage_calculation(
                pages_with_annotations, total_pages
            )
        )
        metrics['layout_coverage'] = self.__safe_percentage_calculation(
            pages_with_layout, total_pages
        )
        
        # Overall coverage (weighted average)
        metrics['overall_coverage'] = (
            metrics['text_coverage'] * 0.4 +
            metrics['table_coverage'] * 0.2 +
            metrics['image_coverage'] * 0.2 +
            metrics['annotation_coverage'] * 0.1 +
            metrics['layout_coverage'] * 0.1
        )
        
        return metrics

    def calculate_toc_coverage(
        self, covered_pages: int, total_pages: int
    ) -> float:
        """Calculate the percentage of pages covered by the TOC."""
        self.__calculations_performed += 1
        return self.__safe_percentage_calculation(covered_pages, total_pages)

    def calculate_section_coverage(
        self, sections_count: int, pages_with_text: int
    ) -> float:
        """Calculate the ratio of parsed sections to pages with text."""
        self.__calculations_performed += 1
        return self.__safe_percentage_calculation(
            sections_count, pages_with_text
        )

    def calculate_toc_pages_covered(
        self, toc_entries: List[Dict[str, Any]], total_pages: int
    ) -> int:
        """Calculate the total number of unique pages covered by TOCs."""
        valid_entries = self.__filter_valid_toc_entries(toc_entries)
        covered_pages = self.__calculate_covered_page_set(
            valid_entries, total_pages
        )
        self.__calculations_performed += 1
        return len(covered_pages)
    
    def calculate_content_quality_score(
        self, pages_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate content quality metrics for the extracted data."""
        self.__calculations_performed += 1
        
        quality_metrics = {
            'total_pages': len(pages_data),
            'pages_with_content': 0,
            'average_content_length': 0,
            'content_diversity_score': 0,
            'extraction_completeness': 0
        }
        
        if not pages_data:
            return quality_metrics
        
        total_content_length = 0
        content_types = set()
        pages_with_content = 0
        
        for page in pages_data:
            page_has_content = False
            page_content_length = 0
            
            # Check text content
            text = page.get('text', '') or ''
            if text.strip():
                page_has_content = True
                page_content_length += len(text)
                content_types.add('text')
            
            # Check tables
            tables = page.get('tables', [])
            if tables:
                page_has_content = True
                content_types.add('tables')
                for table in tables:
                    table_text = table.get('text_representation', '') or ''
                    page_content_length += len(table_text)
            
            # Check images
            images = page.get('images', [])
            if images:
                page_has_content = True
                content_types.add('images')
            
            # Check annotations
            metadata = page.get('metadata', {})
            annotations = metadata.get('annotations', [])
            if annotations:
                page_has_content = True
                content_types.add('annotations')
                for annot in annotations:
                    annot_content = annot.get('content', '') or ''
                    page_content_length += len(annot_content)
            
            if page_has_content:
                pages_with_content += 1
                total_content_length += page_content_length
        
        # Calculate metrics
        quality_metrics['pages_with_content'] = pages_with_content
        quality_metrics['average_content_length'] = (
            total_content_length / pages_with_content 
            if pages_with_content > 0 else 0
        )
        quality_metrics['content_diversity_score'] = len(content_types)
        quality_metrics['extraction_completeness'] = (
            self.__safe_percentage_calculation(
                pages_with_content, len(pages_data)
            )
        )
        
        return quality_metrics

    def __safe_percentage_calculation(
        self, numerator: int, denominator: int
    ) -> float:
        """Calculate a percentage safely, handling division by zero."""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator * 100), 2)

    def __filter_valid_toc_entries(
        self, toc_entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter and sort TOC entries with valid page numbers."""
        valid_entries = [
            entry for entry in toc_entries
            if isinstance(entry.get("page"), int) and entry["page"] > 0
        ]
        return sorted(valid_entries, key=lambda x: x.get("page", 0))

    def __calculate_covered_page_set(
        self, entries: List[Dict[str, Any]], total_pages: int
    ) -> Set[int]:
        """Calculate the set of page numbers covered by TOC entries."""
        covered_pages: Set[int] = set()
        for i, entry in enumerate(entries):
            page_range = self.__get_entry_page_range(
                entry, entries, i, total_pages
            )
            covered_pages.update(page_range)
        return covered_pages

    def __get_entry_page_range(
        self, entry: Dict[str, Any], all_entries: List[Dict[str, Any]],
        current_index: int, total_pages: int
    ) -> range:
        """Determine the page range for a single TOC entry."""
        start = int(entry.get("page", 0))
        
        if current_index + 1 < len(all_entries):
            end = int(all_entries[current_index + 1].get("page", 0)) - 1
        else:
            end = total_pages
        
        return range(start, max(end, start) + 1)
