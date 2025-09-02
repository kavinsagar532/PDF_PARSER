import pdfplumber

def extract_text_from_pdf(pdf_path, start_page=None, end_page=None):
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        start = start_page - 1 if start_page else 0
        end = end_page if end_page else total_pages

        for i in range(start, min(end, total_pages)):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            pages_text.append({
                "page_number": i + 1,
                "text": text
            })
    return pages_text

if __name__ == "__main__":
    pdf_file = "USB_PD_R3_2 V1.1 2024-10.pdf"
    pages = extract_text_from_pdf(pdf_file, start_page=1, end_page=5)
    for p in pages:
        print(f"\n--- Page {p['page_number']} ---\n{p['text'][:500]}")
