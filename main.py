import json
from metadata_parser import MetadataParser
from toc_parser import TOCParser
from section_parser import SectionParser
from helpers import Helper
from validation_report import Validator, ReportGenerator
from extractor import PDFExtractor

def main():
    pdf_file = "USB_PD_R3_2 V1.1 2024-10.pdf"


    metadata_parser = MetadataParser(pdf_file)
    metadata = metadata_parser.parse_metadata()


    validation = Validator.validate_metadata(metadata)
    if validation["is_valid"]:
        print("Metadata is valid.")
    else:
        print("Metadata validation failed with errors:")
        for error in validation["errors"]:
            print(f"- {error}")
        return


    pdf_extractor = PDFExtractor(pdf_file)
    toc_pages = pdf_extractor.extract_text(start_page=1, end_page=20)
    toc_parser = TOCParser(doc_title=metadata.get("doc_title", "Unknown"))
    toc_entries = toc_parser.parse_toc(toc_pages)
    toc_file = "usb_pd_toc.jsonl"
    Helper.write_jsonl(toc_file, toc_entries)


    section_parser = SectionParser(pdf_file, toc_file=toc_file)
    sections_file = "usb_pd_spec.jsonl"
    section_parser.parse_sections()

    ReportGenerator.generate_validation_report(toc_file, sections_file)

    print("PDF parsing complete. Outputs:")
    print(f"- Metadata: usb_pd_metadata.jsonl")
    print(f"- Table of Contents: {toc_file}")
    print(f"- Sections: {sections_file}")

if __name__ == "__main__":
    main()
