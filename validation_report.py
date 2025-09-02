import re
import json
import pandas as pd

def generate_validation_report(toc_file, sections_file, output_excel="validation_report.xlsx"):

    toc_entries = []
    with open(toc_file, "r", encoding="utf-8") as f:
        for line in f:
            toc_entries.append(json.loads(line))


    section_entries = []
    with open(sections_file, "r", encoding="utf-8") as f:
        for line in f:
            section_entries.append(json.loads(line))


    summary = {
        "Total ToC Sections": len(toc_entries),
        "Total Parsed Sections": len(section_entries),
        "Missing Sections": 0,
        "Extra Sections": 0
    }

    toc_ids = [entry["section_id"] for entry in toc_entries]
    parsed_ids = [entry["section_id"] for entry in section_entries]

    missing_sections = [sid for sid in toc_ids if sid not in parsed_ids]
    extra_sections = [sid for sid in parsed_ids if sid not in toc_ids]

    summary["Missing Sections"] = len(missing_sections)
    summary["Extra Sections"] = len(extra_sections)


    with pd.ExcelWriter(output_excel) as writer:
        pd.DataFrame([summary]).to_excel(writer, sheet_name="Summary", index=False)
        pd.DataFrame({"Missing Sections": missing_sections}).to_excel(writer, sheet_name="Missing Sections", index=False)
        pd.DataFrame({"Extra Sections": extra_sections}).to_excel(writer, sheet_name="Extra Sections", index=False)

    print(f"Validation report generated: {output_excel}")
    print("Summary:", summary)


def validate_metadata(metadata):
    report = {
        "is_valid": True,
        "errors": []
    }


    mandatory_fields = ["doc_title", "revision", "version", "release_date"]
    for field in mandatory_fields:
        if field not in metadata or not metadata[field]:
            report["is_valid"] = False
            report["errors"].append(f"Missing or empty field: {field}")


    if "revision" in metadata:
        if not re.match(r"^\d+(\.\d+)?$", str(metadata["revision"])):
            report["is_valid"] = False
            report["errors"].append(f"Invalid revision format: {metadata['revision']}")


    if "version" in metadata:
        if not re.match(r"^\d+(\.\d+)?$", str(metadata["version"])):
            report["is_valid"] = False
            report["errors"].append(f"Invalid version format: {metadata['version']}")


    if "release_date" in metadata:
        if not re.match(r"^\d{4}-\d{2}$", str(metadata["release_date"])):
            report["is_valid"] = False
            report["errors"].append(f"Invalid release_date format: {metadata['release_date']}")

    return report


if __name__ == "__main__":
    with open("usb_pd_metadata.jsonl", "r") as f:
        metadata = json.loads(f.readline().strip())

    validation = validate_metadata(metadata)
    print(json.dumps(validation, indent=4))
