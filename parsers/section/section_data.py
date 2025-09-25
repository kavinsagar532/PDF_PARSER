"""A module defining the data structure for a document section.

This module contains the `Section` dataclass, which serves as standardized
container for all information related to a single parsed section of the
document.
"""

# Standard library imports
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Section:
    """A data class representing a single, parsed section of the document.

    This class is a simple data container with no business logic. Using a
    dataclass provides benefits like automatic `__init__`, `__repr__`, and
    `__eq__` methods.
    """
    doc_title: str  # The main title of the document.
    section_id: str  # The unique identifier, e.g., "1.2.3".
    title: str  # The title of the section, e.g., "Introduction".
    full_path: str  # The combined section ID and title.
    page: int  # The page number where the section begins.
    level: int  # The hierarchical depth of the section.
    parent_id: Optional[str]  # The section_id of the parent, if any.
    content: str  # The full text content of the section.
    tags: List[str] = field(default_factory=list)  # associated tags.
