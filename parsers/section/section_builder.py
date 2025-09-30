"""A module responsible for constructing `Section` objects.

This module provides the `SectionBuilder` class, which acts as factory for
creating `Section` data objects. It encapsulates the logic assembling a
`Section` from various sources, such as a Table of Contents entry or raw
page data.
"""

# Standard library imports
from typing import Any, Dict, List, Optional

# Local imports
from parsers.section.section_data import Section


class SectionBuilder:
    """Constructs `Section` objects with a focus on encapsulation.

    This class centralizes the logic for creating `Section`. All its
    internal attributes and helper methods are private ensure a clean and
    stable public API.
    """

    def __init__(self, doc_title: str):
        self.__doc_title = doc_title
        self.__sections_created = 0

    @property
    def sections_created(self) -> int:
        """Return the total number of `Section` objects created."""
        return self.__sections_created

    def build_from_toc_entry(
        self, entry: Dict[str, Any], content: str
    ) -> Section:
        """Build a `Section` object from a structured TOC entry."""
        section_metadata = self.__extract_section_metadata(entry)
        
        # Ensure content is not None
        safe_content = content if content is not None else ""
        
        section = Section(
            doc_title=entry.get("doc_title") or self.__doc_title,
            section_id=section_metadata["section_id"],
            title=entry.get("title", "") or "",
            full_path=section_metadata["full_path"],
            page=int(entry.get("page", 0)),
            level=section_metadata["level"],
            parent_id=section_metadata["parent_id"],
            tags=entry.get("tags", []) or [],
            content=safe_content,
        )
        
        self.__sections_created += 1
        return section

    def build_comprehensive_page_section(
        self, page_number: int, content: str, heading: Optional[str] = None
    ) -> Section:
        """Build a comprehensive `Section` object with enhanced content analysis."""
        title = heading or f"Enhanced Page {page_number}"
        
        # Ensure content is not None
        safe_content = content if content is not None else ""
        
        # Analyze content for additional metadata
        content_analysis = self.__analyze_content(safe_content)
        
        # Create enhanced tags based on content
        tags = self.__generate_content_tags(safe_content, content_analysis)
        
        section = Section(
            doc_title=self.__doc_title,
            section_id=f"Page-{page_number}",
            title=title,
            full_path=f"Page-{page_number} {title}",
            page=page_number,
            level=1,
            parent_id=None,
            tags=tags,
            content=safe_content,
        )
        
        self.__sections_created += 1
        return section
    
    def __analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content to extract metadata and characteristics."""
        analysis = {
            'has_tables': 'TABLES' in content or '|' in content,
            'has_images': 'IMAGES' in content or 'Image' in content,
            'has_annotations': 'ANNOTATIONS' in content,
            'has_layout_text': 'LAYOUT TEXT' in content,
            'content_length': len(content),
            'line_count': content.count('\n'),
            'section_markers': content.count('==='),
        }
        return analysis
    
    def __generate_content_tags(self, content: str, analysis: Dict[str, Any]) -> List[str]:
        """Generate tags based on content analysis."""
        tags = ['enhanced_extraction']
        
        if analysis.get('has_tables'):
            tags.append('contains_tables')
        if analysis.get('has_images'):
            tags.append('contains_images')
        if analysis.get('has_annotations'):
            tags.append('contains_annotations')
        if analysis.get('has_layout_text'):
            tags.append('has_layout_info')
        
        # Content size tags
        content_length = analysis.get('content_length', 0)
        if content_length > 5000:
            tags.append('large_content')
        elif content_length > 1000:
            tags.append('medium_content')
        else:
            tags.append('small_content')
        
        return tags

    def __extract_section_metadata(
        self, entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract and calculate metadata like level and parent_id."""
        section_id = entry.get("section_id", "") or ""
        level = len(section_id.split(".")) if section_id else 1
        
        parent_id = None
        if section_id and "." in section_id:
            parent_id = ".".join(section_id.split(".")[:-1])
        
        title = entry.get('title', '') or ""
        full_path = f"{section_id} {title}".strip()
        
        return {
            "section_id": section_id,
            "level": level,
            "parent_id": parent_id,
            "full_path": full_path,
        }
