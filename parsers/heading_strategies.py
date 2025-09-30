"""A module for heading detection using a Strategy design pattern.

This module defines a set of classes that work together to identify
headings in text. It uses a polymorphic approach where a
`HeadingDetector` class can leverage multiple `HeadingStrategyInterface`
implementations to find the best match for a given line of text.
"""

# Standard library imports
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

# Local imports
from core.interfaces import HeadingStrategyInterface


class BaseHeadingStrategy(HeadingStrategyInterface, ABC):
    """An abstract base class for heading detection strategies.

    This class uses the Template Method pattern. The `matches` serves
    as the template, handling the counting logic and calling the abstract
    `_is_match` method, which must be implemented by subclasses.
    """

    def __init__(self, name: str):
        self.__name = name
        self.__matches_found = 0
        self.__total_checks = 0

    @property
    def strategy_name(self) -> str:
        """Return the unique name of this strategy."""
        return self.__name

    @property
    def matches_found(self) -> int:
        """Return the number of times this strategy has found a match."""
        return self.__matches_found

    @property
    def total_checks(self) -> int:
        """Return the total number of times this strategy has been checked."""
        return self.__total_checks

    def matches(self, text_line: str) -> bool:
        """Template method to check for a match and update counters."""
        self.__total_checks += 1
        if self._is_match(text_line):
            self.__matches_found += 1
            return True
        return False

    @abstractmethod
    def _is_match(self, text_line: str) -> bool:
        """The core matching logic to be implemented by subclasses."""
        raise NotImplementedError

    def get_confidence(self, text_line: str) -> float:
        """Return a default confidence score. Can be overridden."""
        return 1.0 if self.matches(text_line) else 0.0


class NumberedHeadingStrategy(BaseHeadingStrategy):
    """Detects headings that start with a number (e.g., '1.2.3 Title')."""

    def __init__(self):
        super().__init__("NumberedHeading")
        self.__pattern = re.compile(r"^\d+(\.\d+)*\s+\S+")

    def _is_match(self, text_line: str) -> bool:
        """Check if the line matches the numbered heading pattern."""
        if not self.__is_valid_input(text_line):
            return False
        return bool(self.__pattern.match(text_line.strip()))

    def get_confidence(self, text_line: str) -> float:
        """Return a confidence score based on the numbering depth."""
        if not self.matches(text_line):
            return 0.0
        dots = text_line.count('.')
        return min(1.0, 0.6 + (dots * 0.2))

    def __is_valid_input(self, text_line: str) -> bool:
        """Check if the input line is a processable string."""
        return isinstance(text_line, str) and bool(text_line)


class AllCapsHeadingStrategy(BaseHeadingStrategy):
    """Detects headings that are written in all capital letters."""

    def __init__(self, min_length: int = 4, min_alpha_chars: int = 2):
        super().__init__("AllCapsHeading")
        self.__pattern = re.compile(r"^[A-Z0-9\s\-\(\/]{4,}$")
        self.__min_length = min_length
        self.__min_alpha_chars = min_alpha_chars

    def _is_match(self, text_line: str) -> bool:
        """Return True if the line meets all-caps criteria."""
        if not self.__is_valid_input(text_line):
            return False
        line = text_line.strip()
        return (
            self.__meets_pattern_requirements(line) and
            self.__has_sufficient_caps(line)
        )

    def get_confidence(self, text_line: str) -> float:
        """Return a confidence score based on the ratio of uppercase ."""
        if not self.matches(text_line):
            return 0.0
        return min(1.0, self.__calculate_upper_ratio(text_line))

    def __is_valid_input(self, text_line: str) -> bool:
        """Check if the input line is a processable string."""
        return isinstance(text_line, str) and bool(text_line)

    def __meets_pattern_requirements(self, line: str) -> bool:
        """Check if the line matches the basic all-caps pattern."""
        return bool(self.__pattern.match(line))

    def __has_sufficient_caps(self, line: str) -> bool:
        """Check if the line contains a minimum number of uppercase letters."""
        upper_count = sum(1 for char in line if char.isalpha() and char.isupper())
        return upper_count >= self.__min_alpha_chars

    def __calculate_upper_ratio(self, text: str) -> float:
        """Calculate the ratio of uppercase to total alphabetic characters."""
        alpha_chars = sum(1 for char in text if char.isalpha())
        if alpha_chars == 0:
            return 0.0
        upper_chars = sum(1 for char in text if char.isalpha() and char.isupper())
        return upper_chars / alpha_chars


class MixedCapHeadingStrategy(BaseHeadingStrategy):
    """Detects headings in Title Case or with mixed capitalization."""

    def __init__(self, min_words: int = 2):
        super().__init__("MixedCapHeading")
        self.__min_words = min_words

    def _is_match(self, text_line: str) -> bool:
        """Check if the line appears to be a title-cased heading."""
        if not self.__is_valid_input(text_line):
            return False
        words = self.__extract_words(text_line)
        return (
            self.__meets_word_count_requirement(words) and
            self.__has_sufficient_capitalization(words)
        )

    def get_confidence(self, text_line: str) -> float:
        """confidence score based on the ratio of capitalized words."""
        if not self.matches(text_line):
            return 0.0
        words = self.__extract_words(text_line)
        return self.__calculate_capitalization_ratio(words)

    def __is_valid_input(self, text_line: str) -> bool:
        """Check if the input line is a processable string."""
        return isinstance(text_line, str) and bool(text_line)

    def __extract_words(self, text_line: str) -> List[str]:
        """Split a line of text into a list of words."""
        return text_line.split()

    def __meets_word_count_requirement(self, words: List[str]) -> bool:
        """Check if the number of words meets the minimum threshold."""
        return len(words) >= self.__min_words

    def __has_sufficient_capitalization(self, words: List[str]) -> bool:
        """Check if a sufficient number of words are capitalized."""
        capitalized_count = self.__count_capitalized_words(words)
        threshold = max(1, len(words) // 2)
        return capitalized_count >= threshold

    def __count_capitalized_words(self, words: List[str]) -> int:
        """Count words that start with a capital letter or digit."""
        return sum(1 for word in words if word and (word[0].isupper() or word[0].isdigit()))

    def __calculate_capitalization_ratio(self, words: List[str]) -> float:
        """Calculate the ratio of capitalized words to total words."""
        if not words:
            return 0.0
        return self.__count_capitalized_words(words) / len(words)


class HeadingDetector:
    """A composite class that manages and applies heading strategies."""

    def __init__(self,strategies:Optional[List[HeadingStrategyInterface]]=None):
        self.__strategies = strategies or self.__create_default_strategies()
        self.__total_detections = 0

    @property
    def strategies(self) -> List[HeadingStrategyInterface]:
        """Return a copy of the list of detection strategies."""
        return self.__strategies.copy()

    def add_strategy(self, strategy: HeadingStrategyInterface) -> None:
        """Add a new heading detection strategy to the detector."""
        if not isinstance(strategy, HeadingStrategyInterface):
            raise TypeError(
                "Strategy must implement HeadingStrategyInterface"
            )
        self.__strategies.append(strategy)

    def detect_heading(self, text_line: str) -> Optional[str]:
        """Find the best matching heading for a line of text."""
        if not text_line or text_line is None:
            return None

        clean_line = text_line.strip()
        best_strategy = self.__find_best_matching_strategy(clean_line)

        if best_strategy:
            self.__total_detections += 1
            return clean_line
        return None

    def get_strategy_stats(self) -> Dict[str, Dict[str, int]]:
        """Return a dictionary with statistics for each strategy."""
        return {
            strategy.strategy_name: {
                "matches_found": strategy.matches_found,
                "total_checks": strategy.total_checks,
            }
            for strategy in self.__strategies
        }

    def __find_best_matching_strategy(
        self, text_line: str
    ) -> Optional[HeadingStrategyInterface]:
        """Iterate through strategies and return the highest confidence."""
        best_strategy = None
        highest_confidence = 0.0

        for strategy in self.__strategies:
            confidence = strategy.get_confidence(text_line)
            if confidence > highest_confidence:
                highest_confidence = confidence
                best_strategy = strategy

        return best_strategy if highest_confidence > 0 else None

    def __create_default_strategies(self) -> List[HeadingStrategyInterface]:
        """Return a list of the default heading detection strategies."""
        return [
            NumberedHeadingStrategy(),
            AllCapsHeadingStrategy(),
            MixedCapHeadingStrategy(),
        ]
