import json
import os
import sys
import time
import requests
import base64
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

CONFIG_PATH = Path("wqb_config.json")
LOG_DIR = Path("wqb_logs")

def load_config() -> dict:
    if "WQB_EMAIL" in os.environ:
        return {
            "email": os.environ["WQB_EMAIL"],
            "password": os.environ["WQB_PASSWORD"],
            "url": os.environ.get("WQB_URL", "https://api.worldquantbrain.com"),
            "headless": os.environ.get("WQB_HEADLESS", "false").lower() == "true",
            "timeout_ms": int(os.environ.get("WQB_TIMEOUT", "300000")),
        }
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
            # Use api URL instead of platform URL
            config["url"] = "https://api.worldquantbrain.com"
            return config
    raise RuntimeError(
        "No credentials found. Set WQB_EMAIL/WQB_PASSWORD env vars "
        "or create wqb_config.json"
    )

class WQBAutomation:
    def __init__(self, config: dict):
        self.config = config
        self.session = requests.Session()
        self.results_log = []
        self.base_url = self.config.get("url", "https://api.worldquantbrain.com")
        self.headers = {}

    def start(self):
        # No longer needs to start a browser
        LOG_DIR.mkdir(exist_ok=True)
        print("[WQB] API Client started")

    def stop(self):
        # No longer needs to stop a browser
        self.session.close()
        print("[WQB] API Client stopped")

    def login(self) -> bool:
        print("[WQB] Logging in via API...")
        try:
            email = self.config["email"]
            pwd = self.config["password"]
            creds = base64.b64encode(f"{email}:{pwd}".encode()).decode()
            
            headers = {
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/json"
            }
            
            res = self.session.post(f"{self.base_url}/authentication", headers=headers)
            
            if res.status_code == 201:
                print("[WQB] Login SUCCESS")
                self.headers = headers
                return True
            else:
                print(f"[WQB] Login FAILED: {res.status_code} {res.text}")
                return False
        except Exception as e:
            print(f"[WQB] Login ERROR: {e}")
            return False

    def submit_alpha(self, formula: str, settings_str: str = None):
        print(f"[WQB] Submitting alpha...")
        if not settings_str:
            settings_str = "TOP3000|Market|0|0.05"
            
        parts = settings_str.split('|')
        universe = parts[0] if len(parts) > 0 else "TOP3000"
        neutralization = parts[1] if len(parts) > 1 else "Market"
        decay = int(parts[2]) if len(parts) > 2 else 0
        truncation = float(parts[3]) if len(parts) > 3 else 0.05

        payload = {
            "type": "REGULAR",
            "settings": {
                "instrumentType": "EQUITY",
                "region": "USA",
                "universe": universe,
                "delay": 1,
                "decay": decay,
                "neutralization": neutralization.upper(),
                "truncation": truncation,
                "pasteurization": "ON",
                "unitHandling": "VERIFY",
                "nanHandling": "OFF",
                "language": "FASTEXPR",
                "visualization": False
            },
            "regular": formula
        }

        try:
            res = self.session.post(f"{self.base_url}/simulations", headers=self.headers, json=payload)
            
            if res.status_code != 201:
                print(f"[WQB] Submit FAILED: {res.status_code} {res.text}")
                return {"error": f"Submission failed: {res.text}"}
                
            sim_url = res.headers.get("Location")
            if not sim_url:
                # Some API versions might return url in body or use different header
                sim_url = res.json().get("url")
            
            if not sim_url:
                print(f"[WQB] Could not find simulation URL in response: {res.headers} {res.text}")
                return {"error": "Could not find simulation URL"}
            
            print(f"[WQB] Simulation started: {sim_url}")
            
            # Poll for completion
            max_wait = self.config.get("timeout_ms", 300000) / 1000
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                poll_res = self.session.get(sim_url, headers=self.headers)
                if poll_res.status_code == 200:
                    data = poll_res.json()
                    status = data.get("status", "")
                    progress = data.get("progress", 0.0)
                    
                    if status in ["COMPLETE", "WARNING", "ERROR"] or progress == 1.0:
                        if status == "ERROR":
                            error_msg = data.get("message", "Unknown error")
                            print(f"[WQB] Simulation ERROR: {error_msg}")
                            return {"error": f"Simulation Error: {error_msg}", "raw_data": data}

                        # Fetch the actual alpha metrics
                        alpha_id = data.get("alpha")
                        if alpha_id:
                            alpha_res = self.session.get(f"{self.base_url}/alphas/{alpha_id}", headers=self.headers)
                            if alpha_res.status_code == 200:
                                alpha_data = alpha_res.json()
                                metrics = self._extract_metrics_from_api(alpha_data, formula, settings_str)
                                self._save_log(metrics)
                                print(f"[WQB] Simulation {status}. Sharpe: {metrics.get('sharpe')}")
                                return metrics
                        
                        # If we couldn't get alpha metrics but simulation is done
                        print(f"[WQB] Simulation finished but could not get alpha metrics: {data}")
                        return {"error": "Simulation finished but could not extract metrics", "raw_data": data}
                    
                    print(f"[WQB] Progress: {progress * 100:.1f}%")
                    time.sleep(5)
                else:
                    print(f"[WQB] Poll FAILED: {poll_res.status_code} {poll_res.text}")
                    time.sleep(5)
                    
            print("[WQB] Simulation TIMEOUT")
            return {"error": "Simulation timed out"}

        except Exception as e:
            print(f"[WQB] Exception during submit: {e}")
            return {"error": str(e)}

    def _extract_metrics_from_api(self, alpha_data: dict, formula: str, settings: str) -> dict:
        is_stats = alpha_data.get("is", {})
        
        return {
            "formula": formula,
            "settings": settings,
            "sharpe": is_stats.get("sharpe", 0.0),
            "fitness": is_stats.get("fitness", 0.0),
            "turnover": is_stats.get("turnover", 0.0),
            "returns": is_stats.get("returns", 0.0),
            "margin": is_stats.get("margin", 0.0),
            "drawdown": is_stats.get("drawdown", 0.0),
            "yearly_stats": [], # We can extract this if needed, but not strictly required for MVP
            "raw_api_response": alpha_data
        }

    def _save_log(self, data: dict):
        # Save a clean version without raw_api_response if we want smaller logs
        clean_data = {k: v for k, v in data.items() if k != 'raw_api_response'}
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = LOG_DIR / f"alpha_result_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=2)
        self.results_log.append(clean_data)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WQB API Automation")
    parser.add_argument("--formula", type=str, help="Formula to test")
    parser.add_argument("--settings", type=str, default="TOP3000|Market|0|0.05", help="Settings string")
    args = parser.parse_args()

    config = load_config()
    auto = WQBAutomation(config)
    auto.start()
    if auto.login():
        if args.formula:
            res = auto.submit_alpha(args.formula, args.settings)
            print(json.dumps(res, indent=2))
        else:
            print("Login successful. Run with --formula to test an alpha.")
    auto.stop()
