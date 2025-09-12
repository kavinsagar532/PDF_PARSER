from metadata_parser import MetadataParser
from toc_parser import TOCParser
from section_parser import SectionParser
from helpers import Helper
from validation_report import ReportGenerator
from extractor import PDFExtractor

def main():
    pdf_file = "USB_PD_R3_2 V1.1 2024-10.pdf"

    # 1) metadata -> usb_pd_metadata.jsonl
    metadata_parser = MetadataParser(pdf_file)
    metadata = metadata_parser.parse_metadata()

    # 2) dump all pages -> usb_pd_pages.jsonl 
    pdf_extractor = PDFExtractor(pdf_file)
    pages_dumped = pdf_extractor.dump_all_pages_jsonl(out_path="usb_pd_pages.jsonl")
    print(f"Raw pages dumped: {pages_dumped}")

    # 3) Parse ToC using first N pages from pages dump
    # read pages
    pages_for_toc = []
    for p in Helper.read_jsonl("usb_pd_pages.jsonl"):
        if p.get("page") and p["page"] <= 60:
            pages_for_toc.append({"page": p["page"], "text": p.get("text", "")})
    toc_parser = TOCParser(doc_title=metadata.get("doc_title", "Universal Serial Bus Power Delivery Specification"))
    toc_entries = toc_parser.parse_toc(pages_for_toc)
    toc_file = "usb_pd_toc.jsonl"
    Helper.write_jsonl(toc_file, toc_entries)

    # 4) Parse sections, writes usb_pd_spec.jsonl
    section_parser = SectionParser(pdf_file, toc_file=toc_file, pages_file="usb_pd_pages.jsonl", doc_title=metadata.get("doc_title"))
    sections_file = "usb_pd_spec.jsonl"
    section_entries = section_parser.parse_sections(toc_entries=toc_entries, out_path=sections_file)

    # 5) Validation report
    ReportGenerator.generate_validation_report(toc_file, sections_file, pages_file="usb_pd_pages.jsonl", output_excel="validation_report.xlsx")

    print("PDF parsing complete. Outputs:")
    print(f"- Metadata: usb_pd_metadata.jsonl")
    print(f"- Pages Dump: usb_pd_pages.jsonl")
    print(f"- Table of Contents: {toc_file}")
    print(f"- Sections: {sections_file}")
    print(f"- Validation report: validation_report.xlsx")

if __name__ == "__main__":
    main()
