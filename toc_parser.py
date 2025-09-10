import re

class TOCParser:
    def __init__(self, doc_title="USB Power Delivery Specification Rev 3.2 V1.1"):
        self.doc_title = doc_title

    def parse_toc(self, pages):
        toc_entries = []

        for page in pages:
            lines = page["text"].splitlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("Figure") or line.startswith("Table"):
                    continue

                parts = line.rsplit(" ", 1)
                if len(parts) != 2 or not parts[1].isdigit():
                    continue

                left, page_str = parts[0], parts[1]
                page_num = int(page_str)

                tokens = left.split(maxsplit=1)
                if len(tokens) < 2:
                    continue
                section_id, title = tokens[0], tokens[1]

                if not re.match(r"^\d+(\.\d+)*$", section_id):
                    continue

                title = re.sub(r"[.·]+", " ", title).strip()

                level = section_id.count(".") + 1
                parent_id = ".".join(section_id.split(".")[:-1]) if "." in section_id else None

                toc_entries.append({
                    "doc_title": self.doc_title,
                    "section_id": section_id,
                    "title": title,
                    "page": page_num, 
                    "level": level,
                    "parent_id": parent_id,
                    "full_path": f"{section_id} {title}"
                })

        print(f"Parsed {len(toc_entries)} ToC entries")
        if toc_entries:
            print("First entry:", toc_entries[0])
            print("Last entry:", toc_entries[-1])
        else:
            print("No ToC entries found. Check regex or ToC formatting.")

        return toc_entries


if __name__ == "__main__":
    from extractor import PDFExtractor
    extractor = PDFExtractor("USB_PD_R3_2 V1.1 2024-10.pdf")
    pages = extractor.extract_text(start_page=10, end_page=25)
    toc_parser = TOCParser()
    toc_entries = toc_parser.parse_toc(pages)
