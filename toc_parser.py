import re
from typing import List, Dict, Tuple


class TOCParser:
    """Parser to extract structured Table of Contents (TOC) entries."""

    def __init__(
        self,
        doc_title: str = "Universal Serial Bus Power Delivery Specification"
    ):
        """
        Initialize TOCParser.

        Args:
            doc_title (str): Document title for produced entries.
        """
        self._doc_title = doc_title

    def _flatten_pages_to_lines(
        self, pages: List[Dict]
    ) -> List[Tuple[int, str]]:
        """
        Convert pages into a list of (page_number, line_text) tuples.

        Args:
            pages (List[Dict]): List of page dictionaries.

        Returns:
            List[Tuple[int, str]]: Flattened list of lines.
        """
        lines = []
        for p in pages:
            page_no = p.get("page") or p.get("page_number") or 0
            text = p.get("text", "") or ""
            for line in text.splitlines():
                lines.append((page_no, line.rstrip()))
        return lines

    def _extract_from_buffer(self, buffer: str) -> Dict:
        """
        Extract section id, title and page from a single line.

        Returns empty dict if no pattern matches.
        """
        buf = buffer.strip()
        patterns = [
            r"^\s*(?P<section_id>\d+(?:\.\d+)*)[)\.\-]?\s*"
            r"(?P<title>.+?)\s*(?:\.{2,}|\s{2,})"
            r"(?P<page>\d{1,4})\s*$",
            r"^\s*(?P<section_id>\d+(?:\.\d+)*)\s+"
            r"(?P<title>.+?)\s+(?P<page>\d{1,4})\s*$",
            r"^\s*(Annex|Appendix)\s+(?P<section_id>[A-Z0-9]+)"
            r"[\.\s-]*\s*(?P<title>.+?)\s*(?:\.{2,}|\s{2,})"
            r"(?P<page>\d{1,4})\s*$",
            r"^(?P<title>.+?)\s*(?:\.{2,}|\s{2,})"
            r"(?P<page>\d{1,4})\s*$",
        ]
        for pat in patterns:
            m = re.match(pat, buf, re.IGNORECASE)
            if m:
                if "Annex" in pat or "Appendix" in pat:
                    sid = f"{m.group(1).capitalize()} {m.group('section_id')}"
                    return {
                        "section_id": sid,
                        "title": m.group("title").strip().strip(". "),
                        "page": int(m.group("page")),
                        "full_path": buf
                    }
                return {
                    "section_id": m.groupdict().get("section_id"),
                    "title": m.group("title").strip().strip(". "),
                    "page": int(m.group("page")),
                    "full_path": buf
                }
        return {}

    def parse_toc(self, pages: List[Dict]) -> List[Dict]:
        """
        Parse TOC entries from PDF pages.

        Args:
            pages (List[Dict]): List of page dicts.

        Returns:
            List[Dict]: Structured TOC entries.
        """
        lines = self._flatten_pages_to_lines(pages)
        start_idx = 0
        for idx, (_, line) in enumerate(lines):
            if re.search(r"\btable of contents\b|\bcontents\b", line,
                         re.IGNORECASE):
                start_idx = idx + 1
                break

        toc_entries: List[Dict] = []
        for page, line in lines[start_idx:]:
            entry = self._extract_from_buffer(line)
            if entry:
                final_entry = {
                    "doc_title": self._doc_title,
                    "section_id": entry.get("section_id"),
                    "title": entry.get("title"),
                    "page": entry.get("page"),
                    "level": (
                        len(entry["section_id"].split("."))
                        if entry.get("section_id") else 1
                    ),
                    "parent_id": (
                        ".".join(entry["section_id"].split(".")[:-1])
                        if entry.get("section_id") and "." in
                        entry["section_id"] else None
                    ),
                    "full_path": entry.get("full_path"),
                }
                toc_entries.append(final_entry)
        return toc_entries


if __name__ == "__main__":
    print("TOCParser module ready")