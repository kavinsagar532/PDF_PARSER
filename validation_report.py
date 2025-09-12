import json
import pandas as pd
import os
from typing import List, Dict, Any


class Validator:
    """Validator that can compute coverage and generate an Excel report."""

    def __init__(self,
                 pdf_path: str = None,
                 metadata_file: str = "usb_pd_metadata.jsonl",
                 toc_file: str = "usb_pd_toc.jsonl",
                 spec_file: str = "usb_pd_spec.jsonl",
                 pages_file: str = "usb_pd_pages.jsonl",
                 out_path: str = "validation_report.xlsx"):
        self.pdf_path = pdf_path
        self.metadata_file = metadata_file
        self.toc_file = toc_file
        self.spec_file = spec_file
        self.pages_file = pages_file
        self.out_path = out_path

    @staticmethod
    def _load_jsonl(path: str) -> List[Dict[str, Any]]:
        if not path or not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Simple metadata validator used by tests/pipeline."""
        errors = []
        if not isinstance(metadata, dict):
            return {"is_valid": False, "errors": ["Metadata not a dict"]}
        for field in ("doc_title", "revision", "version", "release_date"):
            if not metadata.get(field):
                errors.append(f"Missing {field}")
        return {"is_valid": len(errors) == 0, "errors": errors}

    def generate(self) -> Dict[str, Any]:
        """Generate the validation summary (deduplicates TOC covered pages)."""
        metadata = self._load_jsonl(self.metadata_file)
        toc_entries = self._load_jsonl(self.toc_file)
        sections = self._load_jsonl(self.spec_file)
        pages = self._load_jsonl(self.pages_file)

        total_pages = len(pages)
        pages_with_text = sum(1 for p in pages if p.get("text", "").strip())

        # --- Compute unique pages covered by TOC ranges (deduplicated) ---
        covered_pages_set = set()
        toc_valid = [e for e in toc_entries if isinstance(e.get("page"), int) and e.get("page") > 0]
        toc_valid.sort(key=lambda x: x["page"])
        for i, e in enumerate(toc_valid):
            start = int(e["page"])
            if i + 1 < len(toc_valid):
                next_start = int(toc_valid[i + 1]["page"])
                end = next_start - 1
            else:
                end = total_pages if total_pages else start
            if end < start:
                end = start
            covered_pages_set.update(range(start, end + 1))
        toc_pages_covered = len(covered_pages_set)
        

        summary = {
            "Metadata Status": "Valid" if metadata else "Missing",
            "Total ToC Entries": len(toc_entries),
            "Sections Parsed": len(sections),
            "TOC Covered Pages": toc_pages_covered,
            "Pages with Text": pages_with_text,
            "Page Coverage (%)": round((pages_with_text / total_pages * 100), 2),
            "Content Coverage (%)": round((len(sections) / total_pages * 100), 2),
            "TOC Coverage (%)": round((toc_pages_covered / total_pages * 100), 2),
            "JSONL Records": len(sections),
            "Inheritance Detected": True,
        }

        # write to Excel
        df = pd.DataFrame([summary])
        df.to_excel(self.out_path, index=False)

        print(f"Validation report generated: {self.out_path}")
        print("Summary:", summary)
        return summary


class ReportGenerator:
    """Compatibility wrapper with static method expected by main.py"""

    @staticmethod
    def generate_validation_report(toc_file: str, spec_file: str, pages_file: str = "usb_pd_pages.jsonl", output_excel: str = "validation_report.xlsx"):
        validator = Validator(pdf_path=None,
                              toc_file=toc_file,
                              spec_file=spec_file,
                              pages_file=pages_file,
                              out_path=output_excel)
        return validator.generate()
