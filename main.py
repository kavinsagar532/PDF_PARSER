import json
from extractor import extract_text_from_pdf
from metadata_parser import parse_metadata
from toc_parser import parse_toc
from section_parser import parse_sections
from validation_report import validate_metadata
from helpers import write_jsonl
import pandas as pd
from validation_report import generate_validation_report

def main():
    pdf_file = "USB_PD_R3_2 V1.1 2024-10.pdf"


    metadata_file = "usb_pd_metadata.jsonl"
    parse_metadata(pdf_file, output_file=metadata_file)


    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.loads(f.readline().strip())


    validation = validate_metadata(metadata)
    if validation["is_valid"]:
        print("Metadata is valid.")
    else:
        print("Metadata validation failed with errors:")
        for error in validation["errors"]:
            print(f"- {error}")
        return


    toc_pages = extract_text_from_pdf(pdf_file, start_page=0, end_page=20)

    toc_entries = parse_toc(
        toc_pages, 
        doc_title=metadata.get("doc_title", "Unknown")
    )


    toc_file = "usb_pd_toc.jsonl"
    write_jsonl(toc_file, toc_entries)


    sections_file = "usb_pd_spec.jsonl"
    parse_sections(pdf_file, toc_file=toc_file, output_file=sections_file)

    print("PDF parsing complete. Outputs:")
    print(f"- Metadata: {metadata_file}")
    print(f"- Table of Contents: {toc_file}")
    print(f"- Sections: {sections_file}")

    generate_validation_report(toc_file, sections_file)


if __name__ == "__main__":
    main()
