import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import RAW_DATA_DIR
from wqb_automation import WQBAutomation, load_config

def crawl_datasets_and_fields(delay=1, instrument_type="EQUITY", region="USA", universe="TOP3000"):
    """
    Crawl all available datasets and their data fields from WorldQuant Brain API.
    """
    config = load_config()
    config["headless"] = True
    auto = WQBAutomation(config)
    
    output_dir = RAW_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    auto.start()
    if not auto.login():
        print("Failed to login to WQB.")
        auto.stop()
        return

    print(f"Fetching datasets for {instrument_type} in {region} (Universe: {universe})...")
    
    datasets = []
    offset = 0
    limit = 20
    
    # 1. Fetch all datasets
    while True:
        url = f"https://api.worldquantbrain.com/data-sets?delay={delay}&instrumentType={instrument_type}&region={region}&universe={universe}&limit={limit}&offset={offset}"
        res = auto.session.get(url, headers=auto.headers)
        
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            datasets.extend(results)
            print(f"Fetched {len(results)} datasets (Offset: {offset})...")
            
            if len(results) < limit:
                break
            offset += limit
        else:
            print(f"Error fetching datasets: {res.status_code} {res.text}")
            break
            
        time.sleep(1) # Be nice to API

    # Save datasets list
    datasets_file = output_dir / "datasets.json"
    with open(datasets_file, "w", encoding="utf-8") as f:
        json.dump(datasets, f, indent=2)
    print(f"Saved {len(datasets)} datasets to {datasets_file}")

    # 2. Fetch data fields for each dataset
    print("\nFetching data fields for each dataset...")
    fields_data = {}
    
    for ds in datasets:
        ds_id = ds["id"]
        ds_name = ds.get("name", "Unknown")
        print(f"Fetching fields for dataset: {ds_name} ({ds_id})...")
        
        fields = []
        f_offset = 0
        f_limit = 20
        
        while True:
            f_url = f"https://api.worldquantbrain.com/data-fields?dataset.id={ds_id}&delay={delay}&instrumentType={instrument_type}&region={region}&universe={universe}&limit={f_limit}&offset={f_offset}"
            res = auto.session.get(f_url, headers=auto.headers)
            
            if res.status_code == 200:
                data = res.json()
                f_results = data.get("results", [])
                fields.extend(f_results)
                
                if len(f_results) < f_limit:
                    break
                f_offset += f_limit
            elif res.status_code == 429:
                print("Rate limited. Waiting 10 seconds...")
                time.sleep(10)
                continue
            else:
                print(f"Error fetching fields for {ds_id}: {res.status_code} {res.text}")
                break
                
            time.sleep(0.5) # Rate limiting

        fields_data[ds_id] = fields
        print(f"  -> Found {len(fields)} fields.")
        
        # Save individual dataset fields
        with open(output_dir / f"fields_{ds_id}.json", "w", encoding="utf-8") as f:
            json.dump(fields, f, indent=2)

    # Compile a master list of all fields
    all_fields = []
    for f_list in fields_data.values():
        all_fields.extend(f_list)
        
    master_file = output_dir / "all_fields.json"
    with open(master_file, "w", encoding="utf-8") as f:
        json.dump(all_fields, f, indent=2)
        
    print(f"\nCompleted! Saved a total of {len(all_fields)} data fields to {master_file}.")
    auto.stop()

if __name__ == "__main__":
    crawl_datasets_and_fields()
