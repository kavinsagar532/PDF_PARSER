import json
from extractor import PDFExtractor
from helpers import Helper

class SectionParser:
    def __init__(self, pdf_file, toc_file="usb_pd_toc.jsonl", output_file="usb_pd_spec.jsonl"):
        self.pdf_file = pdf_file
        self.toc_file = toc_file
        self.output_file = output_file
        self.extractor = PDFExtractor(pdf_file)

    def load_toc(self):
        toc_entries = []
        with open(self.toc_file, "r", encoding="utf-8") as f:
            for line in f:
                toc_entries.append(json.loads(line))
        return toc_entries

    def parse_sections(self):
        toc = self.load_toc()
        pages = self.extractor.extract_text()  # full page coverage

        page_map = {p["page_number"]: p["text"] for p in pages}

        section_entries = []
        for i, entry in enumerate(toc):
            start_page = entry["page"]
            end_page = toc[i + 1]["page"] if i + 1 < len(toc) else max(page_map.keys())
            collected_text = [page_map[p] for p in range(start_page, end_page) if p in page_map]

            entry_with_content = entry.copy()
            entry_with_content["content"] = "\n".join(collected_text).strip()
            section_entries.append(entry_with_content)

        Helper.write_jsonl(self.output_file, section_entries)
        print(f"Parsed {len(section_entries)} sections into {self.output_file}")
        return section_entries

if __name__ == "__main__":
    parser = SectionParser("USB_PD_R3_2 V1.1 2024-10.pdf")
    parser.parse_sections()
