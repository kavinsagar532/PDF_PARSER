import re
from extractor import PDFExtractor
from helpers import Helper

class MetadataParser:
    """Extracts basic metadata fields from the first pages of the specification PDF."""

    def __init__(self, pdf_file: str, output_file: str = "usb_pd_metadata.jsonl"):
        self.pdf_file = pdf_file
        self.output_file = output_file
        self.extractor = PDFExtractor(pdf_file)

    def parse_metadata(self) -> dict:
        pages = self.extractor.extract_text(start_page=1, end_page=5)
        text = "\n".join([p.get("text", "") for p in pages])
        title_match = re.search(r"(Universal Serial Bus.*Power Delivery Specification)", text, re.IGNORECASE)
        revision_match = re.search(r"(?:Revision|Rev\.?)[: ]+\s*([0-9.]+)", text, re.IGNORECASE)
        version_match = re.search(r"(?:Version|V)\s*[:]?[\s]*([0-9.]+)", text, re.IGNORECASE)
        release_match = re.search(r"(?:Release Date|Published|Published:?)\s*[:]?[\s]*([0-9]{4}(?:-[0-9]{1,2})?)", text, re.IGNORECASE)

        metadata = {
            "doc_title": title_match.group(1).strip() if title_match else "Universal Serial Bus Power Delivery Specification",
            "revision": revision_match.group(1) if revision_match else "Unknown",
            "version": version_match.group(1) if version_match else "Unknown",
            "release_date": release_match.group(1) if release_match else "Unknown",
        }

        Helper.write_jsonl(self.output_file, [metadata], mode="w")
        print(f"Metadata extracted and saved to {self.output_file}")
        return metadata

if __name__ == "__main__":
    parser = MetadataParser("USB_PD_R3_2 V1.1 2024-10.pdf")
    parser.parse_metadata()
