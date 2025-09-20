"""File handling utilities for JSON Lines format."""

# Standard library imports
import json
from typing import Any, Dict, List


class JSONLHandler:
    """Enhanced JSON Lines file handler with better error handling."""
    
    def __init__(self):
        self._files_written = 0
        self._files_read = 0
        self._encoding = "utf-8"
    
    @property
    def files_written(self) -> int:
        """Get number of files written."""
        return self._files_written
    
    @property
    def files_read(self) -> int:
        """Get number of files read."""
        return self._files_read
    
    def write_jsonl(self, filename: str, data: List[Dict]) -> int:
        """Write data to JSONL file with error handling."""
        try:
            with open(filename, "w", encoding=self._encoding) as file:
                count = 0
                for item in data:
                    json.dump(item, file, ensure_ascii=False)
                    file.write("\n")
                    count += 1
            
            self._files_written += 1
            return count
        except (IOError, TypeError, ValueError) as e:
            print(f"Error writing JSONL file {filename}: {e}")
            return 0
    
    def read_jsonl(self, filename: str) -> List[Dict]:
        """Read data from JSONL file with error handling."""
        try:
            data = []
            with open(filename, "r", encoding=self._encoding) as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        item = json.loads(line)
                        data.append(item)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line {line_num} in {filename}: {e}")
                        continue
            
            self._files_read += 1
            return data
        except (IOError, FileNotFoundError) as e:
            print(f"Error reading JSONL file {filename}: {e}")
            return []
    
    def append_jsonl(self, filename: str, item: Dict) -> bool:
        """Append single item to JSONL file."""
        try:
            with open(filename, "a", encoding=self._encoding) as file:
                json.dump(item, file, ensure_ascii=False)
                file.write("\n")
            return True
        except (IOError, TypeError, ValueError) as e:
            print(f"Error appending to JSONL file {filename}: {e}")
            return False
    
    def validate_jsonl_file(self, filename: str) -> Dict[str, Any]:
        """Validate JSONL file format and return statistics."""
        stats = {
            "valid_lines": 0,
            "invalid_lines": 0,
            "empty_lines": 0,
            "total_lines": 0,
            "is_valid": True
        }
        
        try:
            with open(filename, "r", encoding=self._encoding) as file:
                for line_num, line in enumerate(file, 1):
                    stats["total_lines"] += 1
                    
                    if not line.strip():
                        stats["empty_lines"] += 1
                        continue
                    
                    try:
                        json.loads(line.strip())
                        stats["valid_lines"] += 1
                    except json.JSONDecodeError:
                        stats["invalid_lines"] += 1
                        stats["is_valid"] = False
        
        except (IOError, FileNotFoundError):
            stats["is_valid"] = False
        
        return stats