import time
import sys
from wqb_automation import WQBAutomation, load_config

CANDIDATES = [
    {
        "name": "Earnings Yield Momentum (Doc Example Var 1)",
        "formula": "group_rank(ts_rank(ts_backfill(anl4_afv4_eps_mean, 60) / close, 60), industry)",
        "settings": "TOP3000|Industry|3|0.08"
    },
    {
        "name": "Operating Earnings Yield (Doc Example Var 1)",
        "formula": "group_rank(ts_rank(operating_income / close, 252), industry)",
        "settings": "TOP3000|Industry|3|0.08"
    },
    {
        "name": "Appreciation of Liabilities (Doc Example Var 1)",
        "formula": "-ts_rank(liabilities, 252)",
        "settings": "TOP3000|Industry|3|0.08"
    },
    {
        "name": "Cashflow to Assets Rank",
        "formula": "group_rank(ts_rank(cashflow_op / assets, 252), industry)",
        "settings": "TOP3000|Industry|3|0.08"
    },
    {
        "name": "Retained Earnings Yield",
        "formula": "group_rank(ts_rank(retained_earnings / close, 252), industry)",
        "settings": "TOP3000|Industry|3|0.08"
    },
    {
        "name": "Short-Term Sentiment Volume Stability",
        "formula": "group_rank(-ts_std_dev(scl12_buzz, 10), industry)",
        "settings": "TOP3000|Industry|3|0.08"
    }
]

def main():
    config = load_config()
    auto = WQBAutomation(config)
    auto.start()
    
    if auto.login():
        print(f"\nStarting Search for 1 Gold Alpha...")
        for alpha in CANDIDATES:
            print(f"\nTesting: {alpha['name']}...")
            try:
                res = auto.submit_alpha(alpha['formula'], alpha['settings'], auto_submit=False, name=alpha['name'])
                sharpe = res.get('sharpe', 0)
                fitness = res.get('fitness', 0)
                
                print(f"Result -> Sharpe: {sharpe}, Fitness: {fitness}, Status: {res.get('status', 'FAIL/REJECTED')}")
                
                if sharpe is not None and sharpe >= 1.25 and fitness >= 1.0:
                    print(f"*** FOUND GOLD ALPHA! ***\nName: {alpha['name']}\nSharpe: {sharpe}\nFitness: {fitness}")
                    print("Exiting search script.")
                    auto.stop()
                    sys.exit(0)
            except Exception as e:
                print(f"Error testing {alpha['name']}: {e}")
            
            print("Sleeping 10s before next test...")
            time.sleep(10)
            
        print("Finished all candidates without finding a Gold Alpha.")
        
    auto.stop()

if __name__ == "__main__":
    main()
