"""Enhanced file I/O utilities with improved encapsulation."""

# Standard library imports
import json
import os
from typing import Dict, Generator, Iterable

# Local imports
from interfaces import FileIOInterface


class JSONLHandler(FileIOInterface):
    """Enhanced JSONL file handler with better encapsulation."""
    
    def __init__(self, encoding: str = "utf-8"):
        self._encoding = encoding
        self._files_written = 0
        self._files_read = 0
        self._max_line_length = 1000000 
    
    @property
    def encoding(self) -> str:
        """Get file encoding."""
        return self._encoding
    
    @property
    def files_written_count(self) -> int:
        """Get number of files written."""
        return self._files_written
    
    @property
    def files_read_count(self) -> int:
        """Get number of files read."""
        return self._files_read
    
    def write_jsonl(self, file_path: str, data: Iterable[Dict], 
                   mode: str = "w") -> int:
        """Write iterable of dictionaries to JSONL file."""
        self._validate_write_parameters(file_path, data, mode)
        
        written_count = 0
        try:
            with open(file_path, mode, encoding=self._encoding) as file:
                for entry in data:
                    json_line = self._serialize_entry(entry)
                    file.write(json_line + "\n")
                    written_count += 1
            
            self._files_written += 1
            print(f"Saved {written_count} entries to {file_path}")
            return written_count
            
        except (IOError, json.JSONEncodeError) as e:
            print(f"Error writing to {file_path}: {e}")
            return 0
    
    def read_jsonl(self, file_path: str) -> Generator[Dict, None, None]:
        """Read JSONL file and yield dictionaries."""
        self._validate_read_parameters(file_path)
        
        try:
            with open(file_path, "r", encoding=self._encoding) as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        if self._is_valid_line(line):
                            yield json.loads(line.strip())
                    except json.JSONDecodeError as e:
                        self._handle_parse_error(file_path, line_num, e)
                        continue
            
            self._files_read += 1
            
        except IOError as e:
            print(f"Error reading {file_path}: {e}")
            return
    
    def _serialize_entry(self, entry: Dict) -> str:
        """Serialize dictionary entry to JSON string."""
        return json.dumps(entry, ensure_ascii=False)
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line is valid for processing."""
        return (line.strip() and 
                len(line) <= self._max_line_length)
    
    def _handle_parse_error(self, file_path: str, line_num: int, 
                           error: json.JSONDecodeError) -> None:
        """Handle JSON parsing errors."""
        print(f"Error parsing line {line_num} in {file_path}: {error}")
    
    def _validate_write_parameters(self, file_path: str, data: Iterable[Dict], 
                                 mode: str) -> None:
        """Validate parameters for write operations."""
        if not file_path or not isinstance(file_path, str):
            raise ValueError("Invalid file path")
        if data is None:
            raise ValueError("Data cannot be None")
        if mode not in ["w", "a"]:
            raise ValueError("Mode must be 'w' or 'a'")
    
    def _validate_read_parameters(self, file_path: str) -> None:
        """Validate parameters for read operations."""
        if not file_path or not isinstance(file_path, str):
            raise ValueError("Invalid file path")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")


# Backwards compatibility
class Helper(JSONLHandler):
    """Backwards compatibility wrapper for JSONLHandler."""
    
    @staticmethod
    def write_jsonl(filename: str, data: Iterable[Dict], 
                   mode: str = "w") -> int:
        """Static method for backwards compatibility."""
        handler = JSONLHandler()
        return handler.write_jsonl(filename, data, mode)
    
    @staticmethod
    def read_jsonl(filename: str) -> Generator[Dict, None, None]:
        """Static method for backwards compatibility."""
        handler = JSONLHandler()
        return handler.read_jsonl(filename)
