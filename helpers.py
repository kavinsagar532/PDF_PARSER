import json
from typing import Iterable, Dict, Generator


class Helper:
    """Helper class for JSONL read/write operations."""

    @staticmethod
    def write_jsonl(filename: str, data: Iterable[Dict], mode: str = "w") -> int:
        """
        Write iterable of dictionaries to a JSONL file.

        Args:
            filename (str): Output JSONL filename.
            data (Iterable[Dict]): Iterable of dict entries to write.
            mode (str): File open mode, default is "w".

        Returns:
            int: Number of entries written.
        """
        written = 0
        with open(filename, mode, encoding="utf-8") as f:
            for entry in data:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                written += 1
        print(f"Saved {written} entries to {filename}")
        return written

    @staticmethod
    def read_jsonl(filename: str) -> Generator[Dict, None, None]:
        """
        Read a JSONL file and yield dictionaries.

        Args:
            filename (str): JSONL file path.

        Yields:
            Dict: Dictionary from each line.
        """
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)