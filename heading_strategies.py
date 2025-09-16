"""Enhanced heading detection strategies with improved OOP design."""

# Standard library imports
import re
from typing import Dict, List, Optional


# Local imports
from interfaces import HeadingStrategyInterface


class BaseHeadingStrategy(HeadingStrategyInterface):
    """Base class for heading detection strategies."""
    
    def __init__(self, name: str):
        self._name = name
        self._matches_found = 0
        self._total_checks = 0
    
    @property
    def strategy_name(self) -> str:
        """Get strategy name."""
        return self._name
    
    @property
    def matches_found(self) -> int:
        """Get number of matches found."""
        return self._matches_found
    
    @property
    def total_checks(self) -> int:
        """Get total number of checks performed."""
        return self._total_checks
    
    def get_confidence(self, text_line: str) -> float:
        """Get confidence score for heading detection."""
        if self.matches(text_line):
            return 1.0
        return 0.0
    
    def _increment_match(self) -> None:
        """Increment match counter."""
        self._matches_found += 1
    
    def _increment_check(self) -> None:
        """Increment total check counter."""
        self._total_checks += 1


class NumberedHeadingStrategy(BaseHeadingStrategy):
    """Strategy for detecting numbered headings (e.g., '1.2.3 Title')."""
    
    def __init__(self):
        super().__init__("NumberedHeading")
        self._pattern = re.compile(r"^\d+(\.\d+)*\s+\S+")
    
    def matches(self, text_line: str) -> bool:
        """Check if line matches numbered heading pattern."""
        self._increment_check()
        
        if not self._is_valid_input(text_line):
            return False
        
        is_match = bool(self._pattern.match(text_line.strip()))
        if is_match:
            self._increment_match()
        return is_match
    
    def get_confidence(self, text_line: str) -> float:
        """Get confidence score based on numbering structure."""
        if not self.matches(text_line):
            return 0.0
        
        # Higher confidence for deeper numbering (1.2.3 vs 1)
        dots = text_line.count('.')
        return min(1.0, 0.6 + (dots * 0.2))
    
    def _is_valid_input(self, text_line: str) -> bool:
        """Check if input is valid for processing."""
        return text_line and isinstance(text_line, str)


class AllCapsHeadingStrategy(BaseHeadingStrategy):
    """Strategy for detecting all-caps headings."""
    
    def __init__(self, min_length: int = 4, min_alpha_chars: int = 2):
        super().__init__("AllCapsHeading")
        self._pattern = re.compile(r"^[A-Z0-9\s\-\(\)/]{4,}$")
        self._min_length = min_length
        self._min_alpha_chars = min_alpha_chars
    
    @property
    def min_length(self) -> int:
        """Get minimum length requirement."""
        return self._min_length
    
    def matches(self, text_line: str) -> bool:
        """Check if line matches all-caps heading pattern."""
        self._increment_check()
        
        if not self._is_valid_input(text_line):
            return False
        
        line = text_line.strip()
        
        if not self._meets_pattern_requirements(line):
            return False
        
        is_match = self._has_sufficient_caps(line)
        if is_match:
            self._increment_match()
        return is_match
    
    def get_confidence(self, text_line: str) -> float:
        """Get confidence score based on caps ratio."""
        if not self.matches(text_line):
            return 0.0
        
        upper_ratio = self._calculate_upper_ratio(text_line)
        return min(1.0, upper_ratio)
    
    def _is_valid_input(self, text_line: str) -> bool:
        """Check if input is valid for processing."""
        return text_line and isinstance(text_line, str)
    
    def _meets_pattern_requirements(self, line: str) -> bool:
        """Check if line meets basic pattern requirements."""
        return bool(self._pattern.match(line))
    
    def _has_sufficient_caps(self, line: str) -> bool:
        """Check if line has sufficient uppercase characters."""
        upper_count = sum(1 for char in line 
                         if char.isalpha() and char.isupper())
        return upper_count >= self._min_alpha_chars
    
    def _calculate_upper_ratio(self, text: str) -> float:
        """Calculate ratio of uppercase to total alphabetic characters."""
        alpha_chars = sum(1 for char in text if char.isalpha())
        if alpha_chars == 0:
            return 0.0
        
        upper_chars = sum(1 for char in text 
                         if char.isalpha() and char.isupper())
        return upper_chars / alpha_chars


class MixedCapHeadingStrategy(BaseHeadingStrategy):
    """Strategy for detecting mixed-case title headings."""
    
    def __init__(self, min_words: int = 2):
        super().__init__("MixedCapHeading")
        self._min_words = min_words
    
    @property
    def min_words(self) -> int:
        """Get minimum words requirement."""
        return self._min_words
    
    def matches(self, text_line: str) -> bool:
        """Check if line matches mixed-case heading pattern."""
        self._increment_check()
        
        if not self._is_valid_input(text_line):
            return False
        
        words = self._extract_words(text_line)
        
        if not self._meets_word_count_requirement(words):
            return False
        
        is_match = self._has_sufficient_capitalization(words)
        if is_match:
            self._increment_match()
        return is_match
    
    def get_confidence(self, text_line: str) -> float:
        """Get confidence score based on capitalization ratio."""
        if not self.matches(text_line):
            return 0.0
        
        words = self._extract_words(text_line)
        cap_ratio = self._calculate_capitalization_ratio(words)
        return cap_ratio
    
    def _is_valid_input(self, text_line: str) -> bool:
        """Check if input is valid for processing."""
        return text_line and isinstance(text_line, str)
    
    def _extract_words(self, text_line: str) -> List[str]:
        """Extract words from text line."""
        return [word for word in text_line.split() if word]
    
    def _meets_word_count_requirement(self, words: List[str]) -> bool:
        """Check if word count meets minimum requirement."""
        return len(words) >= self._min_words
    
    def _has_sufficient_capitalization(self, words: List[str]) -> bool:
        """Check if sufficient words are capitalized."""
        capitalized_count = self._count_capitalized_words(words)
        threshold = max(1, len(words) // 2)
        return capitalized_count >= threshold
    
    def _count_capitalized_words(self, words: List[str]) -> int:
        """Count words that start with capital or digit."""
        return sum(1 for word in words 
                  if word and (word[0].isupper() or word[0].isdigit()))
    
    def _calculate_capitalization_ratio(self, words: List[str]) -> float:
        """Calculate ratio of capitalized to total words."""
        if not words:
            return 0.0
        
        capitalized = self._count_capitalized_words(words)
        return capitalized / len(words)


class HeadingDetector:
    """Composite class managing multiple heading detection strategies."""
    
    def __init__(self, strategies: Optional[List[HeadingStrategyInterface]] = None):
        self._strategies = strategies or self._create_default_strategies()
        self._total_detections = 0
    
    @property
    def strategies(self) -> List[HeadingStrategyInterface]:
        """Get list of strategies."""
        return self._strategies.copy()
    
    @property
    def total_detections(self) -> int:
        """Get total number of successful detections."""
        return self._total_detections
    
    def add_strategy(self, strategy: HeadingStrategyInterface) -> None:
        """Add a new heading detection strategy."""
        if not isinstance(strategy, HeadingStrategyInterface):
            raise TypeError("Strategy must implement HeadingStrategyInterface")
        self._strategies.append(strategy)
    
    def detect_heading(self, text_line: str) -> Optional[str]:
        """Detect if line is a heading using any available strategy."""
        if not text_line:
            return None
        
        clean_line = text_line.strip()
        best_strategy = self._find_best_matching_strategy(clean_line)
        
        if best_strategy:
            self._total_detections += 1
            return clean_line
        
        return None
    
    def get_strategy_stats(self) -> Dict[str, Dict[str, int]]:
        """Get detailed statistics for each strategy."""
        return {
            strategy.strategy_name: {
                "matches_found": strategy.matches_found,
                "total_checks": getattr(strategy, 'total_checks', 0)
            }
            for strategy in self._strategies
        }
    
    def _find_best_matching_strategy(self, text_line: str) -> Optional[HeadingStrategyInterface]:
        """Find the strategy with highest confidence."""
        best_strategy = None
        highest_confidence = 0.0
        
        for strategy in self._strategies:
            confidence = strategy.get_confidence(text_line)
            if confidence > highest_confidence:
                highest_confidence = confidence
                best_strategy = strategy
        
        return best_strategy if highest_confidence > 0 else None
    
    def _create_default_strategies(self) -> List[HeadingStrategyInterface]:
        """Create default set of heading strategies."""
        return [
            NumberedHeadingStrategy(),
            AllCapsHeadingStrategy(),
            MixedCapHeadingStrategy()
        ]
