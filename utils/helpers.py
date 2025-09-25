"""File I/O utilities with a focus on JSONL format handling.

This module provides robust, encapsulated `JSONLHandler` class for reading
and writing JSON Lines (JSONL) files, along with a backward-compatibility
wrapper class.
"""

# Standard library imports
import json
import os
from typing import Any, Dict, Generator, Iterable

# Local imports
from core.interfaces import FileIOInterface


class JSONLHandler(FileIOInterface):
    """A handler for reading and writing JSONL files.

    This class implements the FileIOInterface to provide a consistent API
    for file operations. All internal state and helper methods are private
    to prevent unintended external modification.
    """

    def __init__(self, encoding: str = "utf-8"):
        self.__encoding = encoding
        self.__files_written = 0
        self.__files_read = 0
        self.__max_line_length = 1_000_000  # 1 million characters

    @property
    def encoding(self) -> str:
        """Return the file encoding used for read/write operations."""
        return self.__encoding

    @property
    def files_written_count(self) -> int:
        """Return the total number of files written by this handler."""
        return self.__files_written

    @property
    def files_read_count(self) -> int:
        """total number of files read by this handler instance."""
        return self.__files_read

    def write_jsonl(
        self, file_path: str, data: Iterable[Dict[str, Any]], mode: str = "w"
    ) -> int:
        """iterable of dictionaries to a JSONL file, one per line."""
        self.__validate_write_parameters(file_path, data, mode)

        written_count = 0
        try:
            with open(file_path, mode, encoding=self.__encoding) as file:
                for entry in data:
                    json_line = self.__serialize_entry(entry)
                    file.write(json_line + "\n")
                    written_count += 1
            
            self.__files_written += 1
            print(f"Saved {written_count} entries to {file_path}")
            return written_count

        except (IOError, json.JSONEncodeError) as e:
            print(f"Error writing to {file_path}: {e}")
            return 0

    def read_jsonl(
        self, file_path: str
    ) -> Generator[Dict[str, Any], None, None]:
        """Read a JSONL file and yield each line as a dictionary."""
        self.__validate_read_parameters(file_path)

        try:
            with open(file_path, "r", encoding=self.__encoding) as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        if self.__is_valid_line(line):
                            yield json.loads(line.strip())
                    except json.JSONDecodeError as e:
                        self.__handle_parse_error(file_path, line_num, e)
                        continue
            
            self.__files_read += 1

        except IOError as e:
            print(f"Error reading {file_path}: {e}")
            return

    def __serialize_entry(self, entry: Dict[str, Any]) -> str:
        """Serialize a dictionary entry into a JSON string."""
        return json.dumps(entry, ensure_ascii=False)

    def __is_valid_line(self, line: str) -> bool:
        """Check if a line is non-empty and within the max length limit."""
        return line.strip() and len(line) <= self.__max_line_length

    def __handle_parse_error(
        self, file_path: str, line_num: int, error: json.JSONDecodeError
    ) -> None:
        """Log an error for a line that fails to parse as JSON."""
        print(f"Error parsing line {line_num} in {file_path}: {error}")

    def __validate_write_parameters(
        self, file_path: str, data: Iterable[Dict[str, Any]], mode: str
    ) -> None:
        """Validate parameters for the `write_jsonl` method."""
        if not isinstance(file_path, str) or not file_path:
            raise ValueError("File path must be a non-empty string.")
        if data is None:
            raise ValueError("Data iterable cannot be None.")
        if mode not in ["w", "a"]:
            raise ValueError("Write mode must be 'w' or 'a'.")

    def __validate_read_parameters(self, file_path: str) -> None:
        """Validate parameters for the `read_jsonl` method."""
        if not isinstance(file_path, str) or not file_path:
            raise ValueError("File path must be a non-empty string.")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")


# Backwards compatibility
class Helper(JSONLHandler):
    """Provides a backward-compatible, static-method interface.

    Note: For new implementations, it is instantiate and use
    `JSONLHandler` directly for better resource management.
    """

    @staticmethod
    def write_jsonl(
        filename: str, data: Iterable[Dict[str, Any]], mode: str = "w"
    ) -> int:
        """A static wrapper for `JSONLHandler.write_jsonl`."""
        handler = JSONLHandler()
        return handler.write_jsonl(filename, data, mode)

    @staticmethod
    def read_jsonl(filename: str) -> Generator[Dict[str, Any], None, None]:
        """A static wrapper for `JSONLHandler.read_jsonl`."""
        handler = JSONLHandler()
        return handler.read_jsonl(filename)
