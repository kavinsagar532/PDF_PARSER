import re

from extractor import PDFExtractor
from helpers import Helper


class MetadataParser:
    """Extracts metadata fields from the first pages of the PDF."""

    def __init__(
        self, pdf_file: str, output_file: str = "usb_pd_metadata.jsonl"
    ):
        """
        Initialize MetadataParser.

        Args:
            pdf_file (str): Path to PDF file.
            output_file (str): Output JSONL file for metadata.
        """
        self._pdf_file = pdf_file
        self._output_file = output_file
        self._extractor = PDFExtractor(pdf_file)

    def _extract_field(self, pattern: str, text: str, default="Unknown") -> str:
        """
        Extract a field using regex pattern.

        Args:
            pattern (str): Regex pattern to search.
            text (str): Text to search.
            default (str): Default value if pattern not found.

        Returns:
            str: Extracted field value or default.
        """
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    def parse_metadata(self) -> dict:
        """
        Parse metadata from the first few pages of the PDF.

        Returns:
            dict: Metadata dictionary.
        """
        pages = self._extractor.extract_text(start_page=1, end_page=5)
        text = "\n".join([p.get("text", "") for p in pages])

        metadata = {
            "doc_title": self._extract_field(
                r"(Universal Serial Bus.*Power Delivery Specification)",
                text
            ),
            "revision": self._extract_field(
                r"(?:Revision|Rev\.?)[: ]+\s*([0-9.]+)",
                text
            ),
            "version": self._extract_field(
                r"(?:Version|V)\s*[:]?[\s]*([0-9.]+)",
                text
            ),
            "release_date": self._extract_field(
                r"(?:Release Date|Published:?)\s*[:]?[\s]*"
                r"([0-9]{4}(?:-[0-9]{1,2})?)",
                text,
            ),
        }

        Helper.write_jsonl(self._output_file, [metadata], mode="w")
        print(f"Metadata extracted and saved to {self._output_file}")
        return metadata


if __name__ == "__main__":
    parser = MetadataParser("USB_PD_R3_2 V1.1 2024-10.pdf")
    parser.parse_metadata()