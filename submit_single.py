import json
from wqb_automation import WQBAutomation, load_config

formula = """
lookback = 5;
vol = ts_std_dev(returns, 20);
signal = -group_rank(ts_delta(close, lookback) / (vol + 0.001), subindustry);
regime = ts_rank(volume / adv20, 20) > 0.7;
trade_when(regime, signal, -1)
"""
settings = "TOP1000|Subindustry|0|0.05"

def main():
    print(f"Submitting Alpha Formula:\n{formula}\nSettings: {settings}")
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
