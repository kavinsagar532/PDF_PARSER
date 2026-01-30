"""Text processing utilities."""

# Standard library imports
import re
from typing import List, Optional, Tuple

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
    
    def _get_compiled_pattern(self, pattern: str) -> re.Pattern:
        """Get compiled regex pattern with caching."""
        if pattern not in self._pattern_cache:
            self._ensure_cache_size()
            self._pattern_cache[pattern] = re.compile(pattern, re.IGNORECASE)
        return self._pattern_cache[pattern]
    
    def _ensure_cache_size(self) -> None:
        """Ensure pattern cache doesn't exceed maximum size."""
        if len(self._pattern_cache) >= self._max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._pattern_cache))
            del self._pattern_cache[oldest_key]
    
    def _line_contains_any_term(self, line: str, 
                                search_terms: List[str]) -> bool:
        """Check if line contains any of the search terms."""
        for term in search_terms:
            pattern = rf"\b{re.escape(term)}\b"
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
