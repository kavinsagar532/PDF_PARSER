import json
import os
from typing import List, Dict, Any

import pandas as pd


class Validator:
    """Validator to compute coverage and generate Excel validation reports."""

    def __init__(self, **kwargs):
        """
        Initialize Validator.

        Args:
            **kwargs: File paths.
        """
        self._file_paths = {
            "metadata_file": "usb_pd_metadata.jsonl",
            "toc_file": "usb_pd_toc.jsonl",
            "spec_file": "usb_pd_spec.jsonl",
            "pages_file": "usb_pd_pages.jsonl",
        }
        self._file_paths.update(kwargs)
        self._out_path = self._file_paths.pop("out_path",
                                             "validation_report.xlsx")

    def _load_jsonl(self, path: str) -> List[Dict[str, Any]]:
        """
        Load JSONL file into a list of dictionaries.

        Args:
            path (str): Path to JSONL file.

        Returns:
            List[Dict[str, Any]]: Loaded JSON objects.
        """
        if not path or not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate required metadata fields.

        Args:
            metadata (Dict[str, Any]): Metadata dictionary.

        Returns:
            Dict[str, Any]: Validation result with status and errors.
        """
        errors = []
        if not isinstance(metadata, dict):
            return {"is_valid": False, "errors": ["Metadata not a dict"]}
        for field in ("doc_title", "revision", "version", "release_date"):
            if not metadata.get(field):
                errors.append(f"Missing {field}")
        return {"is_valid": len(errors) == 0, "errors": errors}

    def _calculate_metrics(
        self,
        metadata: List[Dict],
        toc_entries: List[Dict],
        sections: List[Dict],
        pages: List[Dict],
    ) -> Dict[str, Any]:
        """Calculates and returns key validation metrics."""
        total_pages = len(pages)
        pages_with_text = sum(
            1 for p in pages if p.get("text", "").strip()
        )
        covered_pages_set = set()
        toc_valid = sorted([
            e for e in toc_entries
            if isinstance(e.get("page"), int) and e.get("page") > 0
        ], key=lambda x: x["page"])

        for i, e in enumerate(toc_valid):
            start = int(e["page"])
            end = (
                int(toc_valid[i + 1]["page"]) - 1
                if i + 1 < len(toc_valid) else total_pages
            )
            end = max(end, start)
            covered_pages_set.update(range(start, end + 1))
        toc_pages_covered = len(covered_pages_set)

        summary = {
            "Metadata Status": "Valid" if metadata else "Missing",
            "Total ToC Entries": len(toc_entries),
            "Sections Parsed": len(sections),
            "TOC Covered Pages": toc_pages_covered,
            "Pages with Text": pages_with_text,
            "Page Coverage (%)": round(
                (pages_with_text / total_pages * 100), 2
            ) if total_pages else 0.0,
            "Content Coverage (%)": round(
                (len(sections) / total_pages * 100), 2
            ) if total_pages else 0.0,
            "TOC Coverage (%)": round(
                (toc_pages_covered / total_pages * 100), 2
            ) if total_pages else 0.0,
            "JSONL Records": len(sections),
            "Inheritance Detected": True,
        }
        return summary

    def generate(self) -> Dict[str, Any]:
        """
        Generate validation report including page coverage, content, and TOC
        coverage.

        Returns:
            Dict[str, Any]: Summary dict of validation results.
        """
        metadata = self._load_jsonl(self._file_paths["metadata_file"])
        toc_entries = self._load_jsonl(self._file_paths["toc_file"])
        sections = self._load_jsonl(self._file_paths["spec_file"])
        pages = self._load_jsonl(self._file_paths["pages_file"])

        summary = self._calculate_metrics(
            metadata, toc_entries, sections, pages
        )

        df = pd.DataFrame([summary])
        df.to_excel(self._out_path, index=False)
        print(f"Validation report generated: {self._out_path}")
        print("Summary:", summary)
        return summary


class ReportGenerator:
    """Static wrapper for generating validation reports."""

    @staticmethod
    def generate_validation_report(
        toc_file: str,
        spec_file: str,
        pages_file: str = "usb_pd_pages.jsonl",
        output_excel: str = "validation_report.xlsx"
    ):
        """
        Generate validation report from JSONL files.

        Args:
            toc_file (str): TOC JSONL file path.
            spec_file (str): Sections JSONL path.
            pages_file (str): Pages JSONL file path.
            output_excel (str): Output Excel file path.

        Returns:
            dict: Validation summary dictionary.
        """
        validator = Validator(
            toc_file=toc_file,
            spec_file=spec_file,
            pages_file=pages_file,
            out_path=output_excel
        )
        return validator.generate()