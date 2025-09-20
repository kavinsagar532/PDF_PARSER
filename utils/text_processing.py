"""Text processing utilities."""

# Standard library imports
import re
from typing import List, Tuple


class TextProcessor:
    """Utility class for common text processing operations."""
    
    def __init__(self):
        self._pattern_cache = {}
        self._max_cache_size = 100
    
    def extract_field_with_regex(self, pattern: str, text: str, 
                                default: str = "Unknown") -> str:
        """Extract field using regex pattern with caching."""
        compiled_pattern = self._get_compiled_pattern(pattern)
        match = compiled_pattern.search(text)
        return match.group(1).strip() if match else default
    
    def split_into_lines(self, text: str) -> List[str]:
        """Split text into clean lines."""
        if not text:
            return []
        return [line.rstrip() for line in text.splitlines()]
    
    def find_content_start(self, lines: List[Tuple[int, str]], 
                          search_terms: List[str]) -> int:
        """Find the starting index based on search terms."""
        for idx, (_, line) in enumerate(lines):
            if self._line_contains_any_term(line, search_terms):
                return idx + 1
        return 0
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        return text.strip()
    
    def extract_numbers(self, text: str) -> List[int]:
        """Extract all numbers from text."""
        return [int(match) for match in re.findall(r'\d+', text)]
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        return ' '.join(text.split())
    
    def remove_extra_spaces(self, text: str) -> str:
        """Remove extra spaces while preserving single spaces."""
        return re.sub(r'\s+', ' ', text).strip()
    
    def extract_page_numbers(self, text: str) -> List[int]:
        """Extract page numbers from text using optimized regex."""
        # Use compiled regex for better performance
        pattern = self._get_compiled_pattern(r'(?:page|p\.?)\s*(\d+)', re.IGNORECASE)
        matches = pattern.findall(text)
        return [int(match) for match in matches]
    
    def _get_compiled_pattern(self, pattern: str, flags: int = re.IGNORECASE) -> re.Pattern:
        """Get compiled regex pattern with caching."""
        cache_key = (pattern, flags)
        if cache_key not in self._pattern_cache:
            self._ensure_cache_size()
            self._pattern_cache[cache_key] = re.compile(pattern, flags)
        return self._pattern_cache[cache_key]
    
    def _ensure_cache_size(self) -> None:
        """Ensure pattern cache doesn't exceed maximum size."""
        if len(self._pattern_cache) >= self._max_cache_size:
            oldest_key = next(iter(self._pattern_cache))
            del self._pattern_cache[oldest_key]
    
    def _line_contains_any_term(self, line: str, 
                               search_terms: List[str]) -> bool:
        """Check if line contains any of the search terms using optimized search."""
        line_lower = line.lower()
        return any(term.lower() in line_lower for term in search_terms)