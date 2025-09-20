"""Enhanced base classes providing common functionality with improved OOP design."""

# Standard library imports
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Optional, Iterator
import time
import logging

# Local imports
from interfaces import ParserInterface, ProcessorInterface


class ProcessingMetrics:
    """Encapsulates processing metrics and statistics."""
    
    def __init__(self):
        self._start_time = None
        self._end_time = None
        self._processed_count = 0
        self._error_count = 0
        self._status = "initialized"
    
    @property
    def processed_count(self) -> int:
        return self._processed_count
    
    @property 
    def error_count(self) -> int:
        return self._error_count
    
    @property
    def status(self) -> str:
        return self._status
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed processing time in seconds."""
        if self._start_time and self._end_time:
            return self._end_time - self._start_time
        elif self._start_time:
            return time.time() - self._start_time
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total = self._processed_count + self._error_count
        return (self._processed_count / total * 100) if total > 0 else 0.0
    
    def start_processing(self) -> None:
        """Mark start of processing."""
        self._start_time = time.time()
        self._status = "running"
    
    def end_processing(self, success: bool = True) -> None:
        """Mark end of processing."""
        self._end_time = time.time()
        self._status = "completed" if success else "failed"
    
    def increment_processed(self) -> None:
        """Increment processed item counter."""
        self._processed_count += 1
    
    def increment_errors(self) -> None:
        """Increment error counter."""
        self._error_count += 1
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._start_time = None
        self._end_time = None
        self._processed_count = 0
        self._error_count = 0
        self._status = "initialized"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "processed_count": self._processed_count,
            "error_count": self._error_count,
            "status": self._status,
            "elapsed_time": self.elapsed_time,
            "success_rate": self.success_rate
        }


class BaseProcessor(ProcessorInterface): 
    """Enhanced base class for all processing components with improved encapsulation."""
    
    def __init__(self, name: Optional[str] = None):
        self._name = name or self.__class__.__name__
        self._metrics = ProcessingMetrics()
        self._logger = self._setup_logger()
        self._config = {}
    
    @property
    def name(self) -> str:
        """Get processor name."""
        return self._name
    
    @property
    def status(self) -> str:
        """Get current processing status."""
        return self._metrics.status
    
    @property
    def error_count(self) -> int:
        """Get number of errors encountered."""
        return self._metrics.error_count
    
    @property
    def processed_count(self) -> int:
        """Get number of items processed."""
        return self._metrics.processed_count
    
    @property
    def success_rate(self) -> float:
        """Get processing success rate."""
        return self._metrics.success_rate
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        stats = self._metrics.to_dict()
        stats["name"] = self._name
        return stats
    
    def configure(self, **kwargs) -> None:
        """Configure processor with keyword arguments."""
        self._config.update(kwargs)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    @contextmanager
    def processing_context(self) -> Iterator[None]:
        """Context manager for processing operations."""
        self._metrics.start_processing()
        try:
            yield
            self._metrics.end_processing(success=True)
        except Exception as e:
            self._metrics.end_processing(success=False)
            self._logger.error(f"Processing failed: {e}")
            raise
    
    def _set_status(self, status: str) -> None:
        """Set processing status."""
        self._metrics._status = status
    
    def _increment_processed(self) -> None:
        """Increment processed item counter."""
        self._metrics.increment_processed()
    
    def _increment_errors(self) -> None:
        """Increment error counter."""
        self._metrics.increment_errors()
    
    def _reset_counters(self) -> None:
        """Reset processing counters."""
        self._metrics.reset()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the processor."""
        logger = logging.getLogger(f"pdf_parser.{self._name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


class ValidationMixin:
    """Mixin class providing validation capabilities."""
    
    def __init__(self):
        self._validation_enabled = True
        self._validation_rules = {}
    
    @property
    def validation_enabled(self) -> bool:
        """Check if input validation is enabled."""
        return self._validation_enabled
    
    def disable_validation(self) -> None:
        """Disable input validation for performance."""
        self._validation_enabled = False
    
    def enable_validation(self) -> None:
        """Enable input validation."""
        self._validation_enabled = True
    
    def add_validation_rule(self, name: str, rule_func) -> None:
        """Add a custom validation rule."""
        self._validation_rules[name] = rule_func
    
    def remove_validation_rule(self, name: str) -> None:
        """Remove a validation rule."""
        self._validation_rules.pop(name, None)
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input using registered rules."""
        if not self._validation_enabled:
            return True
        
        if input_data is None:
            return False
        
        # Apply custom validation rules
        for rule_name, rule_func in self._validation_rules.items():
            if not rule_func(input_data):
                return False
        
        return True


class BaseParser(BaseProcessor, ParserInterface, ValidationMixin):
    """Enhanced base class for all parser components with validation capabilities."""
    
    def __init__(self, name: Optional[str] = None):
        BaseProcessor.__init__(self, name)
        ValidationMixin.__init__(self)
        self._cached_results = {}
        self._cache_enabled = False
    
    @property
    def cache_enabled(self) -> bool:
        """Check if result caching is enabled."""
        return self._cache_enabled
    
    def enable_cache(self) -> None:
        """Enable result caching."""
        self._cache_enabled = True
    
    def disable_cache(self) -> None:
        """Disable result caching."""
        self._cache_enabled = False
        self.clear_cache()
    
    def clear_cache(self) -> None:
        """Clear cached results."""
        self._cached_results.clear()
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        import hashlib
        content = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Any:
        """Get result from cache if available."""
        return self._cached_results.get(cache_key) if self._cache_enabled else None
    
    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache processing result."""
        if self._cache_enabled:
            self._cached_results[cache_key] = result
    
    def _handle_parsing_error(self, error: Exception, context: str) -> None:
        """Handle parsing errors consistently with improved logging."""
        self._increment_errors()
        self._set_status("error")
        self._logger.error(f"Parsing error in {context}: {error}")
    
    @abstractmethod
    def parse(self, input_data: Any) -> Any:
        """Abstract method that must be implemented by subclasses."""
        pass
