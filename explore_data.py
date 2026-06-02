import json
from wqb_automation import WQBAutomation, load_config

def main():
    config = load_config()
    config["headless"] = True
    auto = WQBAutomation(config)
    try:
        auto.start()
        if auto.login():
            print("\n--- Searching for 'analyst estimate' ---")
            res1 = auto.search_data_fields("analyst estimate", limit=10)
            print(json.dumps(res1, indent=2))
            
            print("\n--- Searching for 'sentiment' ---")
            res2 = auto.search_data_fields("sentiment", limit=10)
            print(json.dumps(res2, indent=2))

            print("\n--- Searching for 'options' ---")
            res3 = auto.search_data_fields("options", limit=10)
            print(json.dumps(res3, indent=2))
        else:
            print("Failed to login to WQB.")
    finally:
        auto.stop()

if __name__ == "__main__":
    main()
