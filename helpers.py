import json
from typing import Iterable, Dict, Generator

class Helper:
    """Small helper for JSONL read/write."""

    @staticmethod
    def write_jsonl(filename: str, data: Iterable[Dict], mode: str = "w") -> int:
        written = 0
        with open(filename, mode, encoding="utf-8") as f:
            for entry in data:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                written += 1
        print(f"Saved {written} entries to {filename}")
        return written

    @staticmethod
    def read_jsonl(filename: str) -> Generator[Dict, None, None]:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)
