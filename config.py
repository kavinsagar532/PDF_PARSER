"""Configuration management for the PDF Parser package."""

from typing import Any, Dict, Optional
import os


class Config:
    """Central configuration management class."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "encoding": "utf-8",
        "max_line_length": 1000000,
        "cache_enabled": False,
        "validation_enabled": True,
        "log_level": "INFO",
        "output_format": "jsonl",
        "page_extraction_batch_size": 100,
        "toc_search_depth": 60,
        "min_coverage_ratio": 0.8,
        "extraction_timeout": 300,  # seconds
        "file_extensions": {
            "pdf": ".pdf",
            "metadata": ".jsonl", 
            "toc": ".jsonl",
            "sections": ".jsonl",
            "pages": ".jsonl",
            "report": ".xlsx"
        },
        "default_filenames": {
            "metadata": "usb_pd_metadata.jsonl",
            "toc": "usb_pd_toc.jsonl", 
            "sections": "usb_pd_spec.jsonl",
            "pages": "usb_pd_pages.jsonl",
            "report": "validation_report.xlsx"
        }
    }
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = self.DEFAULT_CONFIG.copy()
        if config_dict:
            self._config.update(config_dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration with dictionary."""
        self._config.update(config_dict)
    
    def get_filename(self, file_type: str) -> str:
        """Get default filename for a file type."""
        return self._config["default_filenames"].get(file_type, f"output.{file_type}")
    
    def get_file_extension(self, file_type: str) -> str:
        """Get file extension for a file type."""
        return self._config["file_extensions"].get(file_type, ".txt")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self._config.copy()
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        config = cls()
        
        # Load environment variables with PDF_PARSER_ prefix
        env_mapping = {
            "PDF_PARSER_ENCODING": "encoding",
            "PDF_PARSER_CACHE_ENABLED": "cache_enabled",
            "PDF_PARSER_VALIDATION_ENABLED": "validation_enabled",
            "PDF_PARSER_LOG_LEVEL": "log_level",
            "PDF_PARSER_TOC_SEARCH_DEPTH": "toc_search_depth",
            "PDF_PARSER_MIN_COVERAGE_RATIO": "min_coverage_ratio"
        }
        
        for env_var, config_key in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                if config_key in ["cache_enabled", "validation_enabled"]:
                    env_value = env_value.lower() in ("true", "1", "yes")
                elif config_key in ["toc_search_depth"]:
                    env_value = int(env_value)
                elif config_key in ["min_coverage_ratio"]:
                    env_value = float(env_value)
                
                config.set(config_key, env_value)
        
        return config
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Config':
        """Create configuration from JSON file."""
        import json
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            return cls(config_dict)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load config from {file_path}: {e}")
            return cls()


# Global configuration instance
config = Config.from_env()