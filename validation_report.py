import re
import json
import pandas as pd

class Validator:
    @staticmethod
    def validate_metadata(metadata):
        report = {"is_valid": True, "errors": []}
        mandatory_fields = ["doc_title", "revision", "version", "release_date"]

        for field in mandatory_fields:
            if field not in metadata or not metadata[field]:
                report["is_valid"] = False
                report["errors"].append(f"Missing or empty field: {field}")

        if "revision" in metadata and not re.match(r"^\d+(\.\d+)?$", str(metadata["revision"])):
            report["is_valid"] = False
            report["errors"].append(f"Invalid revision format: {metadata['revision']}")

        if "version" in metadata and not re.match(r"^\d+(\.\d+)?$", str(metadata["version"])):
            report["is_valid"] = False
            report["errors"].append(f"Invalid version format: {metadata['version']}")

        if "release_date" in metadata and not re.match(r"^\d{4}-\d{2}$", str(metadata["release_date"])):
            report["is_valid"] = False
            report["errors"].append(f"Invalid release_date format: {metadata['release_date']}")

        return report

class ReportGenerator:
    @staticmethod
    def generate_validation_report(toc_file, sections_file, output_excel="validation_report.xlsx"):
        toc_entries = [json.loads(line) for line in open(toc_file, "r", encoding="utf-8")]
        section_entries = [json.loads(line) for line in open(sections_file, "r", encoding="utf-8")]

        toc_ids = [entry["section_id"] for entry in toc_entries]
        parsed_ids = [entry["section_id"] for entry in section_entries]

        summary = {
            "Total ToC Sections": len(toc_entries),
            "Total Parsed Sections": len(section_entries),
            "Missing Sections": len([sid for sid in toc_ids if sid not in parsed_ids]),
            "Extra Sections": len([sid for sid in parsed_ids if sid not in toc_ids])
        }

        with pd.ExcelWriter(output_excel) as writer:
            pd.DataFrame([summary]).to_excel(writer, sheet_name="Summary", index=False)
            pd.DataFrame({"Missing Sections": [sid for sid in toc_ids if sid not in parsed_ids]}).to_excel(writer, sheet_name="Missing Sections", index=False)
            pd.DataFrame({"Extra Sections": [sid for sid in parsed_ids if sid not in toc_ids]}).to_excel(writer, sheet_name="Extra Sections", index=False)

        print(f"Validation report generated: {output_excel}")
        print("Summary:", summary)

if __name__ == "__main__":
    with open("usb_pd_metadata.jsonl", "r") as f:
        metadata = json.loads(f.readline().strip())
    validation = Validator.validate_metadata(metadata)
    print(json.dumps(validation, indent=4))
