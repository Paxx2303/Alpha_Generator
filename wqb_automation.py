import json
import os
import sys
import time
import requests
import base64
import sqlite3
from pathlib import Path

import structlog
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

load_dotenv()
logger = structlog.get_logger()

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
        self.last_login_time = 0

    def start(self):
        # No longer needs to start a browser
        LOG_DIR.mkdir(exist_ok=True)
        logger.info("API Client started")

    def stop(self):
        # No longer needs to stop a browser
        self.session.close()
        logger.info("API Client stopped")

    def login(self) -> bool:
        logger.info("Logging in via API...")
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
                logger.info("Login SUCCESS")
                self.headers = headers
                self.last_login_time = time.time()
                return True
            else:
                logger.error("Login FAILED", status_code=res.status_code, response=res.text)
                return False
        except Exception as e:
            logger.error("Login ERROR", error=str(e))
            return False

    def refresh_login_if_needed(self):
        # Refresh if last login was more than 4 hours ago (14400 seconds)
        if time.time() - self.last_login_time > 14400:
            logger.info("Session expired or missing, refreshing login...")
            self.login()

    def save_raw_response(self, sim_id: str, data: dict):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        try:
            conn = sqlite3.connect(LOG_DIR / "wqb_data.db")
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_simulations (
                    sim_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    data JSON
                )
            ''')
            cursor.execute('''
                INSERT OR IGNORE INTO raw_simulations (sim_id, timestamp, data)
                VALUES (?, ?, ?)
            ''', (sim_id, timestamp, json.dumps(data)))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to save raw response to SQLite", error=str(e))

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def submit_alpha(self, formula: str, settings_str: str = None):
        self.refresh_login_if_needed()
        logger.info("Submitting alpha...")
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
                logger.error("Submit FAILED", status_code=res.status_code, response=res.text)
                return {"error": f"Submission failed: {res.text}"}
                
            sim_url = res.headers.get("Location")
            if not sim_url:
                # Some API versions might return url in body or use different header
                sim_url = res.json().get("url")
            
            if not sim_url:
                logger.error("Could not find simulation URL in response", headers=dict(res.headers), response=res.text)
                return {"error": "Could not find simulation URL"}
            
            sim_id = sim_url.split("/")[-1]
            logger.info("Simulation started", url=sim_url, sim_id=sim_id)
            
            # Poll for completion
            max_wait = self.config.get("timeout_ms", 300000) / 1000
            start_time = time.time()
            
            poll_interval = 2 # Start with 2 seconds, then 5
            
            while time.time() - start_time < max_wait:
                poll_res = self.session.get(sim_url, headers=self.headers)
                if poll_res.status_code == 200:
                    data = poll_res.json()
                    status = data.get("status", "")
                    progress = data.get("progress", 0.0)
                    
                    if status in ["COMPLETE", "WARNING", "ERROR"] or progress == 1.0:
                        if status == "ERROR":
                            self.save_raw_response(sim_id, data)
                            error_msg = data.get("message", "Unknown error")
                            logger.error("Simulation ERROR", message=error_msg)
                            return {"error": f"Simulation Error: {error_msg}", "raw_data": data}

                        # Fetch the actual alpha metrics
                        alpha_id = data.get("alpha")
                        if alpha_id:
                            alpha_res = self.session.get(f"{self.base_url}/alphas/{alpha_id}", headers=self.headers)
                            if alpha_res.status_code == 200:
                                alpha_data = alpha_res.json()
                                metrics = self._extract_metrics_from_api(alpha_data, formula, settings_str)
                                
                                # Only save JSON logs if fitness >= 0.5
                                if metrics.get("fitness", 0) >= 0.5:
                                    self.save_raw_response(sim_id, data)
                                    self._save_log(metrics)
                                
                                # Auto-submit if it passes IS criteria
                                if metrics.get("sharpe", 0) >= 1.25 and metrics.get("fitness", 0) >= 0.5 and 0.01 <= metrics.get("turnover", 1.0) <= 0.7:
                                    logger.info("Alpha meets IS criteria. Attempting to submit...")
                                    submit_res = self._submit_to_exchange(alpha_id)
                                    metrics["submit_status"] = submit_res

                                logger.info("Simulation finished", status=status, sharpe=metrics.get("sharpe"))
                                return metrics
                        
                        # If we couldn't get alpha metrics but simulation is done
                        self.save_raw_response(sim_id, data)
                        logger.warning("Simulation finished but could not get alpha metrics", data=data)
                        return {"error": "Simulation finished but could not extract metrics", "raw_data": data}
                    
                    logger.debug("Progress", progress=f"{progress * 100:.1f}%")
                    time.sleep(poll_interval)
                    poll_interval = 5 # After the first 2s wait, switch to 5s wait to be kinder to the API
                else:
                    logger.error("Poll FAILED", status_code=poll_res.status_code, response=poll_res.text)
                    time.sleep(5)
                    
            logger.error("Simulation TIMEOUT")
            return {"error": "Simulation timed out"}

        except Exception as e:
            logger.error("Exception during submit", error=str(e))
            # Reraise so @retry can catch network exceptions
            raise e

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def search_data_fields(self, search_query: str, limit: int = 20) -> list:
        self.refresh_login_if_needed()
        logger.info(f"Searching data fields for '{search_query}'...")
        try:
            url = f"{self.base_url}/data-fields?instrumentType=EQUITY&region=USA&delay=1&limit={limit}&search={search_query}"
            res = self.session.get(url, headers=self.headers)
            
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                logger.info(f"Found {len(results)} data fields")
                return results
            elif res.status_code == 429:
                logger.warning("Rate limit exceeded while searching data fields")
                raise Exception("Rate limit exceeded")
            else:
                logger.error("Data fields search FAILED", status_code=res.status_code, response=res.text)
                return [{"error": f"Search failed: {res.text}"}]
                
        except Exception as e:
            logger.error("Exception during data fields search", error=str(e))
            raise e

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

    def _submit_to_exchange(self, alpha_id: str) -> dict:
        try:
            submit_url = f"{self.base_url}/alphas/{alpha_id}/submit"
            logger.info("Sending SUBMIT request...", alpha_id=alpha_id)
            res = self.session.post(submit_url, headers=self.headers)
            if res.status_code != 201 and res.status_code != 200:
                logger.warning("Submit POST failed", status=res.status_code, response=res.text)
                return {"status": "FAIL", "reason": res.text}
            
            # Poll for PENDING checks to resolve
            max_wait = 120
            start_time = time.time()
            while time.time() - start_time < max_wait:
                poll_res = self.session.get(f"{self.base_url}/alphas/{alpha_id}", headers=self.headers)
                if poll_res.status_code == 200:
                    data = poll_res.json()
                    checks = data.get("is", {}).get("checks", [])
                    
                    pending = [c for c in checks if c.get("result") == "PENDING"]
                    if not pending:
                        # Submission checks completed
                        failures = [c for c in checks if c.get("result") == "FAIL"]
                        if not failures:
                            logger.info("Submission SUCCESS! All tests passed.", alpha_id=alpha_id)
                            return {"status": "SUCCESS", "checks": checks}
                        else:
                            fail_names = [c.get("name") for c in failures]
                            logger.warning("Submission FAILED checks", alpha_id=alpha_id, failed_checks=fail_names)
                            return {"status": "FAIL_CHECKS", "checks": checks, "failures": failures}
                    
                    time.sleep(2)
                else:
                    logger.warning("Failed to poll alpha status during submit", status=poll_res.status_code)
                    time.sleep(5)
            
            logger.warning("Submit polling TIMEOUT")
            return {"status": "TIMEOUT"}
            
        except Exception as e:
            logger.error("Exception during submit_to_exchange", error=str(e))
            return {"status": "ERROR", "error": str(e)}

    def _save_log(self, data: dict):
        if data.get("fitness", 0.0) < 0.5:
            return
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        try:
            conn = sqlite3.connect(LOG_DIR / "wqb_data.db")
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alpha_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    formula TEXT,
                    settings TEXT,
                    sharpe REAL,
                    fitness REAL,
                    turnover REAL,
                    returns REAL,
                    margin REAL,
                    drawdown REAL,
                    timestamp TEXT,
                    full_data JSON
                )
            ''')
            cursor.execute('''
                INSERT INTO alpha_results (formula, settings, sharpe, fitness, turnover, returns, margin, drawdown, timestamp, full_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get("formula", ""),
                data.get("settings", ""),
                data.get("sharpe", 0.0),
                data.get("fitness", 0.0),
                data.get("turnover", 0.0),
                data.get("returns", 0.0),
                data.get("margin", 0.0),
                data.get("drawdown", 0.0),
                timestamp,
                json.dumps(data)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to save alpha log to SQLite", error=str(e))
        
        self.results_log.append({k: v for k, v in data.items() if k != 'raw_api_response'})

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
