"""A module for managing and accessing PDF page content efficiently.

This module provides the `PageManager` class, which is designed to hold all
page data from a PDF and provide quick, dictionary-based access to the text
content of any page or range of pages.
"""

# Standard library imports
from typing import Any, Dict, List


class PageManager:
    """Manages access to page data with a focus on performance.

    This class pre-processes a list of page data into a dictionary for
    fast lookups. All internal data structures and helper methods are
    private to ensure a clean and stable public API.
    """

    def __init__(self, pages_data: List[Dict[str, Any]]):
        self.__pages_by_number = self.__organize_pages(pages_data)
        self.__total_pages = len(pages_data)

    @property
    def total_pages(self) -> int:
        """Return the total number of pages managed by this instance."""
        return self.__total_pages

    def get_page_content(self, page_number: int) -> str:
        """Return the text content of a single page, or an empty string."""
        page_data = self.__pages_by_number.get(page_number, "")
        
        # Handle both old string format and new dict format
        if isinstance(page_data, str):
            return page_data
        elif isinstance(page_data, dict):
            return page_data.get("text", "")
        else:
            return ""

    def get_content_range(self, start_page: int, end_page: int) -> str:
        """Return the combined text content of a range of pages."""
        # Ensure the page range is valid.
        start = max(1, start_page)
        end = min(self.total_pages, end_page)

        content_parts = [
            self.get_page_content(page_num)
            for page_num in range(start, end + 1)
        ]
        return "\n".join(content_parts).strip()
    
    def get_comprehensive_content_range(
            self, start_page: int, end_page: int
    ) -> str:
        """Return comprehensive content including text, tables, and images 
        for a page range."""
        start = max(1, start_page)
        end = min(self.total_pages, end_page)
        
        content_parts = [
            self.get_comprehensive_page_content(page_num)
            for page_num in range(start, end + 1)
        ]
        # Filter out None values
        content_parts = [part for part in content_parts if part is not None]
        return "\n\n=== PAGE BREAK ===\n\n".join(content_parts).strip()
    
    def get_comprehensive_page_content(
            self, page_number: int
    ) -> str:
        """Return comprehensive content for a single page including 
        all extracted data."""
        page_data = self.__pages_by_number.get(page_number)
        if not page_data:
            return ""
        
        # If it's just a string (old format), return it
        if isinstance(page_data, str):
            return page_data
        
        # If it's a dictionary (new enhanced format), extract all content
        if isinstance(page_data, dict):
            content_parts = []
            
            # Add main text content
            text_content = page_data.get('text', '') or ''
            if text_content and text_content.strip():
                content_parts.append(f"=== TEXT CONTENT ===\n{text_content}")
            
            # Add table content
            tables = page_data.get('tables', [])
            if tables:
                table_content = "\n".join([
                    f"Table {table.get('table_id', i+1)}:\n" +
                    f"{table.get('text_representation', '') or ''}"
                    for i, table in enumerate(tables)
                    if table.get('text_representation', '') or ''
                ])
                if table_content.strip():
                    content_parts.append(f"=== TABLES ===\n{table_content}")
            
            # Add image information
            images = page_data.get('images', [])
            if images:
                image_content = "\n".join([
                    f"Image {img.get('image_id', i+1)}: " +
                    f"{img.get('name', 'unnamed')} "
                    f"({img.get('width', 0)}x{img.get('height', 0)})"
                    for i, img in enumerate(images)
                ])
                content_parts.append(f"=== IMAGES ===\n{image_content}")
            
            # Add layout information
            layout = page_data.get('layout', {})
            if layout and layout.get('text_lines'):
                layout_content = "\n".join([
                    (line.get('text', '') or '') 
                    for line in layout.get('text_lines', [])
                    if (line.get('text', '') or '').strip()
                ])
                if layout_content and layout_content.strip():
                    content_parts.append(
                        f"=== LAYOUT TEXT ===\n{layout_content}"
                    )
            
            # Add annotations
            metadata = page_data.get('metadata', {})
            annotations = metadata.get('annotations', [])
            if annotations:
                annot_content = "\n".join([
                    f"Annotation ({annot.get('type', 'unknown')}): " +
                    f"{annot.get('content', '') or ''}"
                    for annot in annotations 
                    if (annot.get('content', '') or '').strip()
                ])
                if annot_content and annot_content.strip():
                    content_parts.append(
                        f"=== ANNOTATIONS ===\n{annot_content}"
                    )
            
            # Filter out any None values and return joined content
            safe_content_parts = [
                part for part in content_parts if part is not None
            ]
            return "\n\n".join(safe_content_parts)
        
        return str(page_data)

    def __organize_pages(
        self, pages_data: List[Dict[str, Any]]
    ) -> Dict[int, Any]:
        """Convert a list of dictionaries into page_number -> content map."""
        organized = {}
        for page in pages_data:
            page_num = page.get("page", 0)
            # Store the entire page data for comprehensive access
            organized[page_num] = page
        return organized
