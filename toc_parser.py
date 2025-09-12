import re
import json
from typing import List, Dict, Tuple

class TOCParser:
    """Robust TOC parser that produces structured entries with page numbers."""

    def __init__(self, doc_title: str = "Universal Serial Bus Power Delivery Specification"):
        self.doc_title = doc_title

    def _flatten_pages_to_lines(self, pages: List[Dict]) -> List[Tuple[int, str]]:
        lines = []
        for p in pages:
            page_no = p.get("page") or p.get("page_number") or 0
            text = p.get("text", "") or ""
            for line in text.splitlines():
                lines.append((page_no, line.rstrip()))
        return lines

    def _line_ends_with_page(self, line: str) -> bool:
        return bool(re.search(r"(?:\.{2,}|\s{2,})(\d{1,4})\s*$", line)) or bool(re.search(r"\s+(\d{1,4})\s*$", line))

    def _extract_from_buffer(self, buffer: str) -> Dict:
        buf = buffer.strip()
        m = re.match(r"^\s*(?P<section_id>\d+(?:\.\d+)*)[)\.\-]?\s*(?P<title>.+?)\s*(?:\.{2,}|\s{2,})(?P<page>\d{1,4})\s*$", buf)
        if m:
            return {"section_id": m.group("section_id").strip(),
                    "title": m.group("title").strip().strip(". "),
                    "page": int(m.group("page").strip()),
                    "full_path": buf}
        m = re.match(r"^\s*(?P<section_id>\d+(?:\.\d+)*)\s+(?P<title>.+?)\s+(?P<page>\d{1,4})\s*$", buf)
        if m:
            return {"section_id": m.group("section_id").strip(),
                    "title": m.group("title").strip().strip(". "),
                    "page": int(m.group("page").strip()),
                    "full_path": buf}
        m = re.match(r"^\s*(Annex|Appendix)\s+(?P<section_id>[A-Z0-9]+)[\.\s-]*\s*(?P<title>.+?)\s*(?:\.{2,}|\s{2,})(?P<page>\d{1,4})\s*$", buf, re.IGNORECASE)
        if m:
            sid = f"{m.group(1).capitalize()} {m.group('section_id')}"
            return {"section_id": sid,
                    "title": m.group("title").strip().strip(". "),
                    "page": int(m.group("page")),
                    "full_path": buf}
        m = re.match(r"^(?P<title>.+?)\s*(?:\.{2,}|\s{2,})(?P<page>\d{1,4})\s*$", buf)
        if m:
            return {"section_id": None,
                    "title": m.group("title").strip().strip(". "),
                    "page": int(m.group("page")),
                    "full_path": buf}
        return {}

    def parse_toc(self, pages: List[Dict]) -> List[Dict]:
        lines = self._flatten_pages_to_lines(pages)
        if not lines:
            return []

        start_idx = 0
        for idx, (_, line) in enumerate(lines):
            if re.search(r"\btable of contents\b|\bcontents\b", line, re.IGNORECASE):
                start_idx = idx + 1
                break

        toc_entries: List[Dict] = []
        idx = start_idx
        max_idx = len(lines)
        while idx < max_idx:
            page, line = lines[idx]
            entry = self._extract_from_buffer(line)
            if entry:
                # --- Schema fields in exact order ---
                final_entry = {
                    "doc_title": self.doc_title,
                    "section_id": entry.get("section_id"),
                    "title": entry.get("title"),
                    "page": entry.get("page"),
                    "level": len(entry["section_id"].split(".")) if entry.get("section_id") else 1,
                    "parent_id": ".".join(entry["section_id"].split(".")[:-1]) if entry.get("section_id") and "." in entry["section_id"] else None,
                    "full_path": entry.get("full_path")
                }
                toc_entries.append(final_entry)
            idx += 1
        return toc_entries

if __name__ == "__main__":
    print("TOCParser module ready")
