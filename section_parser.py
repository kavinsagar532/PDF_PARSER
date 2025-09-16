import json
import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Section:
    """Dataclass representing a section in the PDF."""
    doc_title: str
    section_id: str
    title: str
    full_path: str
    page: int
    level: int
    parent_id: str
    tags: list
    content: str


class SectionParser:
    """Parser to generate structured sections from TOC and pages JSONL."""

    def __init__(
        self,
        pdf_path: str,
        toc_file: Optional[str] = "usb_pd_toc.jsonl",
        pages_file: Optional[str] = "usb_pd_pages.jsonl",
        doc_title: str = "Universal Serial Bus Power Delivery Specification",
    ):
        """
        Initialize SectionParser.

        Args:
            pdf_path (str): Path to PDF file.
            toc_file (Optional[str]): Path to TOC JSONL file.
            pages_file (Optional[str]): Path to pages JSONL file.
            doc_title (str): Document title.
        """
        self._pdf_path = pdf_path
        self._toc_file = toc_file
        self._pages_file = pages_file
        self._doc_title = doc_title

    def _load_jsonl(self, path: str) -> List[Dict]:
        """
        Load JSONL file into a list of dictionaries.

        Args:
            path (str): Path to JSONL file.

        Returns:
            List[Dict]: List of JSON objects.
        """
        if not path or not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def _is_numbered_heading(self, line: str) -> bool:
        """Return True if line looks like a numbered heading."""
        return bool(re.match(r"^\d+(\.\d+)*\s+\S+", line))

    def _is_all_caps_heading(self, line: str) -> bool:
        """Return True if line is short and mostly uppercase chars."""
        if not re.match(r"^[A-Z0-9\s\-\(\)/]{4,}$", line):
            return False
        upper_count = sum(
            1 for ch in line if ch.isalpha() and ch.isupper()
        )
        return upper_count >= 2

    def _is_mixed_cap_heading(self, line: str) -> bool:
        """Return True if many words start with uppercase or digits."""
        words = [w for w in line.split() if w]
        if len(words) < 2:
            return False
        score = sum(
            1 for w in words if (w and (w[0].isupper() or w[0].isdigit()))
        )
        return score >= max(1, len(words) // 2)

    def _detect_heading_from_text(self, text: str) -> Optional[str]:
        """
        Detect a section heading from a page's text using a
        polymorphic approach.
        """
        if not text:
            return None
        heading_strategies = [
            self._is_numbered_heading,
            self._is_all_caps_heading,
            self._is_mixed_cap_heading
        ]
        for raw in text.splitlines()[:12]:
            line = raw.strip()
            if not line:
                continue
            for strategy in heading_strategies:
                if strategy(line):
                    return line
        return None

    def _get_sections_from_toc(
        self,
        toc_valid: List[Dict],
        pages_by_num: Dict,
        total_pages: int
    ) -> List[Dict]:
        """Helper to build sections based on a valid TOC."""
        sections = []
        for i, entry in enumerate(toc_valid):
            start = int(entry["page"])
            next_page = (
                int(toc_valid[i + 1]["page"])
                if i + 1 < len(toc_valid) else total_pages + 1
            )
            end = max(next_page - 1, start)

            content_parts = [
                pages_by_num.get(pnum, "")
                for pnum in range(start, end + 1)
            ]
            content = "\n".join(content_parts).strip()

            sec_obj = Section(
                doc_title=entry.get("doc_title") or self._doc_title,
                section_id=entry.get("section_id") or "",
                title=entry.get("title") or "",
                full_path=f"{entry.get('section_id', '')} "
                f"{entry.get('title', '')}".strip(),
                page=start,
                level=(
                    len(entry.get("section_id", "").split("."))
                    if entry.get("section_id") else 1
                ),
                parent_id=(
                    ".".join(entry.get("section_id", "").split(".")[:-1])
                    if entry.get("section_id") and "." in
                    entry.get("section_id") else None
                ),
                tags=entry.get("tags", []),
                content=content
            )
            sections.append(vars(sec_obj))
        return sections

    def _get_sections_for_untouched_pages(
        self,
        toc_pages_set: set,
        pages_by_num: Dict,
        total_pages: int
    ) -> List[Dict]:
        """Helper to find and parse sections not in TOC."""
        sections = []
        for p in range(1, total_pages + 1):
            if p in toc_pages_set:
                continue
            text = pages_by_num.get(p, "") or ""
            if not text.strip():
                continue
            heading = self._detect_heading_from_text(text) or f"Page {p}"
            sec_obj = Section(
                doc_title=self._doc_title,
                section_id=f"Page-{p}",
                title=heading,
                full_path=f"Page-{p} {heading}",
                page=p,
                level=1,
                parent_id=None,
                tags=[],
                content=text.strip()
            )
            sections.append(vars(sec_obj))
        return sections

    def parse_sections(
        self,
        toc_entries: Optional[List[Dict]] = None,
        out_path: str = "usb_pd_spec.jsonl"
    ) -> List[Dict]:
        """
        Parse sections from TOC entries and pages JSONL.

        Args:
            toc_entries (Optional[List[Dict]]): TOC entries.
            out_path (str): Output JSONL file path.

        Returns:
            List[Dict]: List of sections.
        """
        pages = self._load_jsonl(self._pages_file)
        total_pages = len(pages)
        if toc_entries is None:
            toc_entries = self._load_jsonl(self._toc_file)

        pages_by_num = {p.get("page"): p.get("text", "") for p in pages}
        toc_valid = sorted([
            e for e in toc_entries
            if isinstance(e.get("page"), int) and e.get("page") > 0
        ], key=lambda x: x["page"])

        sections = self._get_sections_from_toc(
            toc_valid, pages_by_num, total_pages
        )
        toc_pages_set = set()
        for i, entry in enumerate(toc_valid):
            start = int(entry["page"])
            next_page = (
                int(toc_valid[i + 1]["page"])
                if i + 1 < len(toc_valid) else total_pages + 1
            )
            end = max(next_page - 1, start)
            toc_pages_set.update(range(start, end + 1))

        sections.extend(
            self._get_sections_for_untouched_pages(
                toc_pages_set, pages_by_num, total_pages
            )
        )

        sections.sort(
            key=lambda s: (s.get("page", 99999), s.get("section_id") or "")
        )
        with open(out_path, "w", encoding="utf-8") as f:
            for s in sections:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"Parsed {len(sections)} sections into {out_path}")
        return sections


if __name__ == "__main__":
    print("SectionParser module ready")