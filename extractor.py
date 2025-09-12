import json
from typing import List, Dict, Optional
import pdfplumber

class BaseExtractor:
    """Base extractor with common utilities"""
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

class PDFExtractor(BaseExtractor):
    """PDF extraction utilities using pdfplumber.

    - extract_text(start_page, end_page) -> List[Dict] with keys: 'page' and 'text'
    - dump_all_pages_jsonl(out_path) -> writes usb_pd_pages.jsonl with records {"page": n, "text": "..."}
    - total_pages() -> total page count
    """

    def extract_text(self, start_page: Optional[int] = 1, end_page: Optional[int] = None) -> List[Dict]:
        pages_text: List[Dict] = []
        with pdfplumber.open(self.pdf_path) as pdf:
            total = len(pdf.pages)
            if end_page is None or end_page > total:
                end_page = total
            # convert to 0-index
            for i in range(max(1, start_page) - 1, end_page):
                page = pdf.pages[i]
                text = page.extract_text() or ""
                pages_text.append({"page": i + 1, "text": text})
        return pages_text

    def dump_all_pages_jsonl(self, out_path: str = "usb_pd_pages.jsonl") -> int:
        """Dump the entire PDF into JSONL file with records {"page": n, "text": "..."}"""
        count = 0
        with pdfplumber.open(self.pdf_path) as pdf:
            with open(out_path, "w", encoding="utf-8") as f:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    f.write(json.dumps({"page": i, "text": text}, ensure_ascii=False) + "\n")
                    count += 1
        return count

    def total_pages(self) -> int:
        with pdfplumber.open(self.pdf_path) as pdf:
            return len(pdf.pages)


if __name__ == "__main__":
    ext = PDFExtractor("USB_PD_R3_2 V1.1 2024-10.pdf")
    n = ext.dump_all_pages_jsonl()
    print(f"Dumped {n} pages to usb_pd_pages.jsonl")
