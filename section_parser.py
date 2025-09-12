import json
import os
import re
from typing import List, Dict, Optional

class SectionParser:
    """Build sections from TOC entries and pages JSONL.

    Output spec JSONL entries with fields:
    {
        "doc_title": "...",
        "section_id": "...",
        "title": "...",
        "full_path": "...",
        "page": X,
        "level": Y,
        "parent_id": "...",
        "tags": [...],
        "content": "..."
    }
    """

    def __init__(self, pdf_path: str, toc_file: Optional[str] = "usb_pd_toc.jsonl", pages_file: Optional[str] = "usb_pd_pages.jsonl", doc_title: str = "Universal Serial Bus Power Delivery Specification"):
        self.pdf_path = pdf_path
        self.toc_file = toc_file
        self.pages_file = pages_file
        self.doc_title = doc_title

    def _load_jsonl(self, path: str) -> List[Dict]:
        if not path or not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def _detect_heading_from_text(self, text: str) -> Optional[str]:
        """find a reasonable heading/title from page text."""
        if not text:
            return None
        for line in text.splitlines()[:12]:
            l = line.strip()
            if not l:
                continue
            if re.match(r"^\d+(\.\d+)*\s+\S+", l):
                return l
            if re.match(r"^[A-Z0-9\s\-\(\)/]{4,}$", l) and sum(1 for ch in l if ch.isalpha() and ch.isupper()) >= 2:
                return l
            words = [w for w in l.split() if w]
            if len(words) >= 2 and sum(1 for w in words if w[0].isupper() or w[0].isdigit()) >= max(1, len(words)//2):
                return l
        return None

    def parse_sections(self, toc_entries: Optional[List[Dict]] = None, out_path: str = "usb_pd_spec.jsonl") -> List[Dict]:
        pages = self._load_jsonl(self.pages_file)
        total_pages = len(pages)
        if toc_entries is None:
            toc_entries = self._load_jsonl(self.toc_file)

        pages_by_num = {p.get("page"): p.get("text", "") for p in pages}
        toc_valid = [e for e in toc_entries if isinstance(e.get("page"), int) and e.get("page") > 0]
        toc_valid.sort(key=lambda x: x["page"])
        sections: List[Dict] = []
        toc_pages_set = set()

        for i, entry in enumerate(toc_valid):
            page = int(entry["page"])
            end = (int(toc_valid[i + 1]["page"]) - 1) if i + 1 < len(toc_valid) else total_pages
            if end < page:
                end = page

            toc_pages_set.update(range(page, end + 1))
            content_parts = []
            for pnum in range(page, end + 1):
                text = pages_by_num.get(pnum, "")
                if text:
                    content_parts.append(text)
            content = "\n".join(content_parts).strip()

            sec_id = entry.get("section_id") or ""
            title = entry.get("title") or ""
            full_path = f"{sec_id} {title}".strip() if sec_id else title
            level = len(sec_id.split(".")) if sec_id else 1
            parent_id = ".".join(sec_id.split(".")[:-1]) if sec_id and "." in sec_id else None

            sections.append({
                "doc_title": entry.get("doc_title") or self.doc_title,
                "section_id": sec_id,
                "title": title,
                "full_path": full_path,
                "page": page,
                "level": level,
                "parent_id": parent_id,
                "tags": entry.get("tags", []),
                "content": content
            })

        for p in range(1, total_pages + 1):
            if p in toc_pages_set:
                continue
            text = pages_by_num.get(p, "") or ""
            if not text.strip():
                continue
            heading = self._detect_heading_from_text(text) or f"Page {p}"
            sections.append({
                "doc_title": self.doc_title,
                "section_id": f"Page-{p}",
                "title": heading,
                "full_path": f"Page-{p} {heading}",
                "page": p,
                "level": 1,
                "parent_id": None,
                "tags": [],
                "content": text.strip()
            })

        sections.sort(key=lambda s: (s.get("page", 99999), s.get("section_id") or ""))
        with open(out_path, "w", encoding="utf-8") as f:
            for s in sections:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"Parsed {len(sections)} sections into {out_path}")
        return sections


if __name__ == "__main__":
    print("SectionParser module ready")
