import re
from extractor import extract_text_from_pdf
from helpers import write_jsonl

def parse_metadata(pdf_file, output_file="usb_pd_metadata.jsonl"):
    pages = extract_text_from_pdf(pdf_file, start_page=0, end_page=5)

    text = "\n".join([p["text"] for p in pages])


    title_match = re.search(r"(Universal Serial Bus.*Power Delivery Specification)", text, re.IGNORECASE)
    revision_match = re.search(r"Revision[: ]+([0-9.]+)", text, re.IGNORECASE)
    version_match = re.search(r"Version[: ]+([0-9.]+)", text, re.IGNORECASE)
    release_match = re.search(r"Release Date[: ]+([0-9\-A-Za-z]+)", text, re.IGNORECASE)

    metadata = {
        "doc_title": title_match.group(1).strip() if title_match else "Unknown",
        "revision": revision_match.group(1) if revision_match else "Unknown",
        "version": version_match.group(1) if version_match else "Unknown",
        "release_date": release_match.group(1) if release_match else "Unknown",
    }


    write_jsonl(output_file, [metadata])

    print(f"Metadata extracted and saved to {output_file}")
    print(metadata)

if __name__ == "__main__":
    pdf_file = "USB_PD_R3_2 V1.1 2024-10.pdf"
    parse_metadata(pdf_file)
