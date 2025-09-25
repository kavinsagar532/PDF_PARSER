"""A module responsible for constructing `Section` objects.

This module provides the `SectionBuilder` class, which acts as factory for
creating `Section` data objects. It encapsulates the logic assembling a
`Section` from various sources, such as a Table of Contents entry or raw
page data.
"""

# Standard library imports
from typing import Any, Dict, Optional

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
        
        section = Section(
            doc_title=entry.get("doc_title") or self.__doc_title,
            section_id=section_metadata["section_id"],
            title=entry.get("title", ""),
            full_path=section_metadata["full_path"],
            page=int(entry.get("page", 0)),
            level=section_metadata["level"],
            parent_id=section_metadata["parent_id"],
            tags=entry.get("tags", []),
            content=content,
        )
        
        self.__sections_created += 1
        return section

    def build_page_section(
        self, page_number: int, content: str, heading: Optional[str] = None
    ) -> Section:
        """Build a `Section` object for a page that is not in the TOC."""
        title = heading or f"Page {page_number}"
        
        section = Section(
            doc_title=self.__doc_title,
            section_id=f"Page-{page_number}",
            title=title,
            full_path=f"Page-{page_number} {title}",
            page=page_number,
            level=1,
            parent_id=None,
            content=content,
        )
        
        self.__sections_created += 1
        return section

    def __extract_section_metadata(
        self, entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract and calculate metadata like level and parent_id."""
        section_id = entry.get("section_id", "")
        level = len(section_id.split(".")) if section_id else 1
        
        parent_id = None
        if section_id and "." in section_id:
            parent_id = ".".join(section_id.split(".")[:-1])
        
        full_path = f"{section_id} {entry.get('title', '')}".strip()
        
        return {
            "section_id": section_id,
            "level": level,
            "parent_id": parent_id,
            "full_path": full_path,
        }
