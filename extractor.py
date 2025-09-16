import json
from typing import List, Dict, Optional
import pdfplumber


class BaseExtractor:
    """Base extractor class containing common utilities for all extractors."""

    def __init__(self, pdf_path: str):
        """
        Initialize the BaseExtractor.

        Args:
            pdf_path (str): Path to the PDF file to be processed.
        """
        self._pdf_path = pdf_path


class PDFExtractor(BaseExtractor):
    """Extracts text from PDFs using pdfplumber."""

    def extract_text(
        self, start_page: Optional[int] = 1, end_page: Optional[int] = None
    ) -> List[Dict]:
        """
        Extract text from a PDF between specified pages.

        Args:
            start_page (Optional[int]): Starting page number (1-indexed).
            end_page (Optional[int]): Ending page number (inclusive).

        Returns:
            List[Dict]: List of dicts with keys "page" and "text".
        """
        pages_text: List[Dict] = []
        with pdfplumber.open(self._pdf_path) as pdf:
            total = len(pdf.pages)
            if end_page is None or end_page > total:
                end_page = total
            for i in range(max(1, start_page) - 1, end_page):
                page = pdf.pages[i]
                text = page.extract_text() or ""
                pages_text.append({"page": i + 1, "text": text})
        return pages_text

    def _write_pages_to_jsonl(self, pages: List[Dict], out_path: str) -> int:
        """
        Write extracted pages to a JSONL file.

        Args:
            pages (List[Dict]): List of page dictionaries.
            out_path (str): Path to output JSONL file.

        Returns:
            int: Number of pages written.
        """
        count = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for page in pages:
                f.write(json.dumps(page, ensure_ascii=False) + "\n")
                count += 1
        return count

    def dump_all_pages_jsonl(self, out_path: str = "usb_pd_pages.jsonl") -> int:
        """
        Extract all pages and save them to a JSONL file.

        Args:
            out_path (str): Output file path.

        Returns:
            int: Number of pages written.
        """
        pages = self.extract_text()
        count = self._write_pages_to_jsonl(pages, out_path)
        return count

    def total_pages(self) -> int:
        """
        Get the total number of pages in the PDF.

        Returns:
            int: Total page count.
        """
        with pdfplumber.open(self._pdf_path) as pdf:
            return len(pdf.pages)


if __name__ == "__main__":
    extractor = PDFExtractor("USB_PD_R3_2 V1.1 2024-10.pdf")
    n = extractor.dump_all_pages_jsonl()
    print(f"Dumped {n} pages to usb_pd_pages.jsonl")