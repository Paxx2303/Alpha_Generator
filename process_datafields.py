import json
from pathlib import Path

def process_datafields():
    raw_file = Path("alpha_skills/rawdata/all_fields.json")
    output_file = Path("alpha_skills/processed_data/fields_summary.json")
    output_dir = output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not raw_file.exists():
        print(f"File {raw_file} not found. Please run the crawler first.")
        return
        
    print(f"Loading {raw_file}...")
    with open(raw_file, "r", encoding="utf-8") as f:
        fields = json.load(f)
        
    print(f"Processing {len(fields)} fields...")
    processed_fields = []
    
    for f_data in fields:
        # Extract only the useful information for Alpha Generator
        processed = {
            "id": f_data.get("id"),
            "description": f_data.get("description", ""),
            "dataset": f_data.get("dataset", {}).get("name", ""),
            "dataset_id": f_data.get("dataset", {}).get("id", ""),
            "coverage": f_data.get("coverage", 0),
            "userCount": f_data.get("userCount", 0),
            "category": f_data.get("category", {}).get("name", "")
        }
        processed_fields.append(processed)
        
    # Sort by coverage (descending) to prioritize higher quality data
    processed_fields.sort(key=lambda x: x["coverage"], reverse=True)
    
    print(f"Saving {len(processed_fields)} processed fields to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_fields, f, indent=2)
        
    # Create a quick summary text file for easy reading
    text_file = output_dir / "fields_summary.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        for p in processed_fields:
            f.write(f"ID: {p['id']}\n")
            f.write(f"Desc: {p['description']}\n")
            f.write(f"Dataset: {p['dataset']} | Category: {p['category']} | Coverage: {p['coverage']:.2f}\n")
            f.write("-" * 40 + "\n")
            
    print("Done! Data is ready for use by the MCP Server and AI Agent.")

if __name__ == "__main__":
    process_datafields()
