import pdfplumber

class PDFExtractor:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file

    def extract_text(self, start_page=None, end_page=None):
        pages_text = []
        with pdfplumber.open(self.pdf_file) as pdf:
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
    extractor = PDFExtractor("USB_PD_R3_2 V1.1 2024-10.pdf")
    pages = extractor.extract_text(start_page=1, end_page=5)
    for p in pages:
        print(f"\n--- Page {p['page_number']} ---\n{p['text'][:500]}")
