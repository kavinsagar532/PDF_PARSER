import json
from extractor import extract_text_from_pdf
from helpers import write_jsonl

def load_toc(filename="usb_pd_toc.jsonl"):
    """Load the previously saved ToC JSONL into a list of dicts"""
    toc_entries = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            toc_entries.append(json.loads(line))
    return toc_entries

def parse_sections(pdf_file, toc_file="usb_pd_toc.jsonl", output_file="usb_pd_spec.jsonl"):

    toc = load_toc(toc_file)


    pages = extract_text_from_pdf(pdf_file)

    
    page_map = {p["page_number"]: p["text"] for p in pages}


    section_entries = []
    for i, entry in enumerate(toc):
        start_page = entry["page"]
        end_page = toc[i + 1]["page"] if i + 1 < len(toc) else max(page_map.keys())


        collected_text = []
        for page_num in range(start_page, end_page):
            if page_num in page_map:
                collected_text.append(page_map[page_num])

        entry_with_content = entry.copy()
        entry_with_content["content"] = "\n".join(collected_text).strip()
        section_entries.append(entry_with_content)


    write_jsonl(output_file, section_entries)

    print(f"Parsed {len(section_entries)} sections into {output_file}")

if __name__ == "__main__":
    pdf_file = "USB_PD_R3_2 V1.1 2024-10.pdf"
    parse_sections(pdf_file)
