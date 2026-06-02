import json
from wqb_automation import WQBAutomation, load_config

formula = """
quality = ts_rank(operating_profit_before_interest_tax / close, 252);
reversion = rank(-returns);
signal = quality * reversion;
group_rank(signal, subindustry)
"""
settings = "TOP1000|Subindustry|3|0.05"

def main():
    print(f"Submitting Fundamental Alpha Formula:\n{formula}\nSettings: {settings}")
    config = load_config()
    config["headless"] = True
    auto = WQBAutomation(config)
    try:
        auto.start()
        if auto.login():
            res = auto.submit_alpha(formula, settings)
            print("\nRESULT:")
            print(json.dumps(res, indent=2))
        else:
            print("Failed to login to WQB.")
    finally:
        auto.stop()

if __name__ == "__main__":
    main()
