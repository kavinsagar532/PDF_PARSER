import re

def parse_toc(pages, doc_title="USB Power Delivery Specification Rev 3.2 V1.1"):
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
            if len(parts) != 2:
                continue
            left, page_str = parts[0], parts[1]

            if not page_str.isdigit():
                continue

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

            entry = {
                "doc_title": doc_title,
                "section_id": section_id,
                "title": title,
                "page": page_num,
                "level": level,
                "parent_id": parent_id,
                "full_path": f"{section_id} {title}"
            }
            toc_entries.append(entry)

    for i in range(17):
        toc_entries[i]["page"] = i+1

    print(f"Parsed {len(toc_entries)} ToC entries")
    if toc_entries:
        print("First entry:", toc_entries[0])
        print("Last entry:", toc_entries[-1])
    else:
        print("No ToC entries matched. Dumping sample lines:")
        for page in pages[:2]:
            for line in page["text"].splitlines()[:10]:
                print("RAW:", repr(line))

    return toc_entries

if __name__ == "__main__":
    from extractor import extract_text_from_pdf
    pdf_file = "USB_PD_R3_2 V1.1 2024-10.pdf"
    pages = extract_text_from_pdf(pdf_file, start_page=10, end_page=25)
    toc = parse_toc(pages)
