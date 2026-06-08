# process_datafields.py — Process raw WQB field JSON into a summary
import json
import sys
from pathlib import Path

# Ensure repo root is on path so config is importable
sys.path.insert(0, str(Path(__file__).parent))
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR


def process_datafields():
    raw_file   = RAW_DATA_DIR / "all_fields.json"
    output_dir = PROCESSED_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "fields_summary.json"

    if not raw_file.exists():
        print(f"File {raw_file} not found. Please run crawl_datasets.py first.")
        return

    print(f"Loading {raw_file}…")
    fields = json.loads(raw_file.read_text(encoding="utf-8"))
    print(f"Processing {len(fields)} fields…")

    processed_fields = []
    for f_data in fields:
        processed_fields.append({
            "id":         f_data.get("id"),
            "description": f_data.get("description", ""),
            "dataset":    f_data.get("dataset", {}).get("name", ""),
            "dataset_id": f_data.get("dataset", {}).get("id", ""),
            "coverage":   f_data.get("coverage", 0),
            "userCount":  f_data.get("userCount", 0),
            "category":   f_data.get("category", {}).get("name", ""),
        })

    # Sort by coverage descending (higher coverage = more reliable)
    processed_fields.sort(key=lambda x: x["coverage"], reverse=True)

    output_file.write_text(json.dumps(processed_fields, indent=2), encoding="utf-8")
    print(f"Saved {len(processed_fields)} processed fields → {output_file}")

    # Plain-text summary for quick reading
    text_file = output_dir / "fields_summary.txt"
    with text_file.open("w", encoding="utf-8") as f:
        for p in processed_fields:
            f.write(f"ID: {p['id']}\n")
            f.write(f"Desc: {p['description']}\n")
            f.write(f"Dataset: {p['dataset']} | Category: {p['category']} | Coverage: {p['coverage']:.2f}\n")
            f.write("-" * 40 + "\n")

    print("Done! Data ready for MCP Server and AI Agent.")


if __name__ == "__main__":
    process_datafields()
