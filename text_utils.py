"""Text processing utilities - Compatibility module.

This module maintains backward compatibility while redirecting to the new
modular structure in the utils package.
"""

# Import from new modular structure
from utils.text_processing import TextProcessor

# Export for backward compatibility
__all__ = ["TextProcessor"]
