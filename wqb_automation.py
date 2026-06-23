import json
import os
import sys
import time
import requests
import base64
from pathlib import Path

import structlog
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

load_dotenv()
logger = structlog.get_logger()

sys.stdout.reconfigure(line_buffering=True)

CONFIG_PATH = Path("wqb_config.json")
LOG_DIR = Path("wqb_logs")

# v2: lazy-import Store to avoid circular deps if automation is imported early
_store = None

def _get_store():
    global _store
    if _store is None:
        from storage.store import Store
        _store = Store()
    return _store

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
        try:
            formula  = data.get("regular", "")
            settings = data.get("settings", {})
            settings_str = (
                f"{settings.get('universe','TOP3000')}|"
                f"{settings.get('neutralization','Market')}|"
                f"{settings.get('decay',0)}|"
                f"{settings.get('truncation',0.05)}"
            )
            _get_store().save_simulation(sim_id, formula, settings_str,
                                         data.get("status", ""), data)
        except Exception as e:
            logger.error("Failed to save simulation to store", error=str(e))

    def _is_failed_combination(self, formula: str, settings: str) -> bool:
        try:
            return _get_store().is_failed(formula, settings)
        except Exception:
            return False

    def _save_failed_combination(self, metrics: dict):
        try:
            _get_store().save_failed(
                metrics.get("formula", ""),
                metrics.get("settings", ""),
                metrics.get("sharpe", 0),
                metrics.get("fitness", 0),
            )
        except Exception as e:
            logger.error("Failed to save failed combination", error=str(e))

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def submit_alpha(self, formula: str, settings_str: str = None, auto_submit: bool = False, name: str = None):
        self.refresh_login_if_needed()
        logger.info("Submitting alpha simulation...")
        if not settings_str:
            settings_str = "TOP3000|Market|0|0.05"
            
        if self._is_failed_combination(formula, settings_str):
            logger.warning("Rejected: Known failed combination")
            return {"error": "Rejected: Known failed combination"}
            
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
                poll_res = self.session.get(sim_url, headers=self.headers, timeout=30)
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
                            alpha_res = self.session.get(f"{self.base_url}/alphas/{alpha_id}", headers=self.headers, timeout=30)
                            if alpha_res.status_code == 200:
                                alpha_data = alpha_res.json()
                                metrics = self._extract_metrics_from_api(alpha_data, formula, settings_str)
                                
                                # Only save JSON logs if fitness >= 0.5
                                if metrics.get("fitness", 0) >= 0.5:
                                    self.save_raw_response(sim_id, data)
                                    self._save_log(metrics)
                                
                                # Check if it passes IS criteria
                                if metrics.get("sharpe", 0) >= 1.25 and metrics.get("fitness", 0) >= 1.0 and 0.01 <= metrics.get("turnover", 1.0) <= 0.7:
                                    logger.info("Alpha meets IS criteria.")

                                    # ── Full IS check: weight concentration + all hard fails ───
                                    is_check = self.check_all_is_checks(alpha_id)
                                    metrics["is_checks_detail"] = is_check.get("detail", "")
                                    hard_fails = [
                                        c for c in is_check.get("failures", [])
                                        if c.get("name") != "SELF_CORRELATION"
                                    ]
                                    if hard_fails:
                                        fail_names = [c.get("name") for c in hard_fails]
                                        logger.warning("IS hard check FAIL — skipping gold save",
                                                       alpha_id=alpha_id, checks=fail_names)
                                        metrics["status"] = f"FAIL_CHECKS"
                                        self._save_failed_combination(metrics)
                                    else:
                                        # ── Self-correlation check (WQB rule) ──────────────────
                                        corr_info = self.check_self_correlation(alpha_id)
                                        metrics["self_correlation"] = corr_info.get("value")
                                        if corr_info.get("passes") is False:
                                            logger.warning("SELF_CORRELATION FAIL — skipping gold save",
                                                           alpha_id=alpha_id, detail=corr_info["detail"])
                                            metrics["status"] = "CORRELATED"
                                            self._save_failed_combination(metrics)
                                        else:
                                            metrics["name"] = name or "Untitled Alpha"
                                            metrics["status"] = "UNSUBMITTED"
                                            if corr_info.get("value") is not None:
                                                logger.info("Self-correlation OK", corr=corr_info["value"])
                                            if auto_submit:
                                                logger.info("Attempting to submit...")
                                                submit_res = self._submit_to_exchange(alpha_id)
                                                metrics["submit_status"] = submit_res
                                                if submit_res.get("status") == "SUCCESS":
                                                    metrics["status"] = "SUBMITTED_SUCCESS"
                                            self._save_gold_alpha(metrics)
                                else:
                                    # Add to failed combinations if it does not meet gold criteria
                                    self._save_failed_combination(metrics)

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

    def search_data_fields(self, search_query: str, limit: int = 20,
                           force_live: bool = False) -> list:
        """
        Search data fields.  By default reads the local store (fast, offline).
        Falls back to WQB API on cache miss or when force_live=True.
        """
        if not force_live:
            try:
                store = _get_store()
                results = store.query_datafields(
                    region="USA", universe="TOP3000", delay=1,
                    search=search_query, limit=limit,
                )
                if results:
                    logger.info("search_data_fields.from_store",
                                query=search_query, count=len(results))
                    return results
            except Exception as e:
                logger.warning("search_data_fields.store_error", error=str(e))

        # Live API fallback
        return self._search_data_fields_live(search_query, limit)

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def _search_data_fields_live(self, search_query: str, limit: int = 20) -> list:
        self.refresh_login_if_needed()
        logger.info("search_data_fields.live", query=search_query)
        try:
            url = (f"{self.base_url}/data-fields?instrumentType=EQUITY&region=USA"
                   f"&universe=TOP3000&delay=1&limit={limit}&search={search_query}")
            res = self.session.get(url, headers=self.headers)
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                # Cache results in store for next time
                try:
                    for row in results:
                        row.update({"_region":"USA","_universe":"TOP3000","_delay":1})
                    _get_store().upsert_datafields(results)
                except Exception:
                    pass
                return results
            elif res.status_code == 429:
                raise Exception("Rate limit exceeded")
            else:
                logger.error("search_data_fields.live_failed",
                             status=res.status_code, response=res.text[:200])
                return [{"error": f"Search failed: {res.text}"}]
        except Exception as e:
            logger.error("search_data_fields.exception", error=str(e))
            raise e

    def list_operators(self, category: str = None) -> list:
        """Return operators from local store (populated by WQBOperatorCrawler)."""
        try:
            store = _get_store()
            ops = store.list_operators(category=category)
            if ops:
                return ops
        except Exception as e:
            logger.warning("list_operators.store_error", error=str(e))
        # If store empty: inform caller to run the crawler
        return [{"info": "Operators not yet crawled. Run: python run_crawl.py --kind operators"}]

    def _extract_metrics_from_api(self, alpha_data: dict, formula: str, settings: str) -> dict:
        is_stats = alpha_data.get("is", {})

        # Extract self-correlation from IS checks (WQB populates after simulation)
        self_corr = None
        corr_cutoff = 0.7
        for check in is_stats.get("checks", []):
            if check.get("name") == "SELF_CORRELATION":
                self_corr = check.get("value")
                break

        return {
            "id": alpha_data.get("id"),
            "formula": formula,
            "settings": settings,
            "sharpe": is_stats.get("sharpe", 0.0),
            "fitness": is_stats.get("fitness", 0.0),
            "turnover": is_stats.get("turnover", 0.0),
            "returns": is_stats.get("returns", 0.0),
            "margin": is_stats.get("margin", 0.0),
            "drawdown": is_stats.get("drawdown", 0.0),
            "self_correlation": self_corr,
            "yearly_stats": [],
            "raw_api_response": alpha_data
        }

    def check_self_correlation(self, alpha_id: str) -> dict:
        """Fetch self-correlation for a simulated alpha from WQB API.
        Returns {"value": float, "passes": bool, "detail": str}
        """
        try:
            res = self.session.get(f"{self.base_url}/alphas/{alpha_id}", headers=self.headers)
            if res.status_code != 200:
                return {"value": None, "passes": None, "detail": f"HTTP {res.status_code}"}
            data = res.json()
            is_stats = data.get("is", {})
            sharpe = is_stats.get("sharpe", 0.0)
            for check in is_stats.get("checks", []):
                if check.get("name") == "SELF_CORRELATION":
                    val = check.get("value")
                    result = check.get("result", "UNKNOWN")
                    passes = result != "FAIL"
                    val_str = f"{val:.4f}" if val is not None else "None"
                    detail = f"self_corr={val_str} result={result}"
                    if not passes:
                        detail += f" (cutoff=0.7, need Sharpe {sharpe*1.1:.2f}+)"
                    logger.info("Self-correlation check", alpha_id=alpha_id,
                                corr=val, result=result, sharpe=sharpe)
                    return {"value": val, "passes": passes, "detail": detail}
            return {"value": None, "passes": True, "detail": "No SELF_CORRELATION check found"}
        except Exception as e:
            logger.error("self_correlation check failed", error=str(e))
            return {"value": None, "passes": None, "detail": str(e)}

    def check_all_is_checks(self, alpha_id: str) -> dict:
        """Check ALL IS checks (not just self-corr) for hard failures.

        WQB runs multiple checks: WEIGHT_CONCENTRATION, SELF_CORRELATION,
        SHARPE, TURNOVER, LOW_UNIVERSE_COVERAGE, etc.
        Any check with result=FAIL blocks submission.

        Returns {"passes": bool, "failures": [...], "all_checks": [...], "detail": str}
        """
        try:
            res = self.session.get(f"{self.base_url}/alphas/{alpha_id}", headers=self.headers)
            if res.status_code != 200:
                return {"passes": None, "failures": [], "detail": f"HTTP {res.status_code}"}
            data = res.json()
            is_stats = data.get("is", {})
            all_checks = is_stats.get("checks", [])
            failures = [c for c in all_checks if c.get("result") == "FAIL"]
            passes = len(failures) == 0
            detail_parts = []
            for c in all_checks:
                name = c.get("name", "?")
                result = c.get("result", "?")
                val = c.get("value")
                val_str = f"={val:.4f}" if isinstance(val, float) else (f"={val}" if val is not None else "")
                detail_parts.append(f"{name}{val_str}[{result}]")
            detail = " | ".join(detail_parts)
            if failures:
                fail_names = [f"{c.get('name')}={c.get('value')}" for c in failures]
                logger.warning("IS check FAIL", alpha_id=alpha_id, failures=fail_names)
            else:
                logger.info("All IS checks pass/pending", alpha_id=alpha_id)
            return {"passes": passes, "failures": failures, "all_checks": all_checks, "detail": detail}
        except Exception as e:
            logger.error("check_all_is_checks failed", error=str(e))
            return {"passes": None, "failures": [], "detail": str(e)}

    def _submit_to_exchange(self, alpha_id: str) -> dict:
        try:
            submit_url = f"{self.base_url}/alphas/{alpha_id}/submit"
            logger.info("Sending SUBMIT request...", alpha_id=alpha_id)
            res = self.session.post(submit_url, headers=self.headers)

            # ── 201/200: accepted → poll for PENDING checks ────────────────
            if res.status_code in (200, 201):
                max_wait  = 120
                start_time = time.time()
                while time.time() - start_time < max_wait:
                    poll_res = self.session.get(f"{self.base_url}/alphas/{alpha_id}", headers=self.headers)
                    if poll_res.status_code == 200:
                        data   = poll_res.json()
                        checks = data.get("is", {}).get("checks", [])
                        pending = [c for c in checks if c.get("result") == "PENDING"]
                        if not pending:
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

            # ── 403: WQB returns check results inline in the body ──────────
            # This happens when a check (e.g. SELF_CORRELATION) fails immediately.
            if res.status_code == 403:
                try:
                    body = res.json()
                    # Body may itself be a JSON string (double-encoded)
                    is_data = body.get("is", {})
                    if not is_data:
                        # Try parsing the raw text as JSON
                        inner = json.loads(res.text)
                        is_data = inner.get("is", {})
                    checks   = is_data.get("checks", [])
                    failures = [c for c in checks if c.get("result") == "FAIL"]
                    logger.warning("Submit rejected (403) — failed checks:", alpha_id=alpha_id,
                                   failed=[c.get("name") for c in failures])
                    return {"status": "FAIL_CHECKS", "checks": checks, "failures": failures}
                except Exception:
                    pass
                logger.warning("Submit POST failed (403)", status=res.status_code, response=res.text[:300])
                return {"status": "FAIL", "reason": res.text}

            # ── Other error codes ──────────────────────────────────────────
            logger.warning("Submit POST failed", status=res.status_code, response=res.text[:300])
            return {"status": "FAIL", "reason": res.text}

        except Exception as e:
            logger.error("Exception during submit_to_exchange", error=str(e))
            return {"status": "ERROR", "error": str(e)}

    def _save_log(self, data: dict):
        if data.get("fitness", 0.0) < 0.5:
            return
        try:
            _get_store().save_alpha_result(data)
        except Exception as e:
            logger.error("Failed to save alpha result to store", error=str(e))
        self.results_log.append({k: v for k, v in data.items() if k != 'raw_api_response'})

    def _save_gold_alpha(self, metrics: dict):
        try:
            _get_store().upsert_gold_alpha(metrics)
            logger.info("Saved gold alpha to store", id=metrics.get("id"))
        except Exception as e:
            logger.error("Failed to save gold alpha to store", error=str(e))

    def submit_saved_alpha(self, alpha_id: str) -> dict:
        self.refresh_login_if_needed()
        return self._submit_to_exchange(alpha_id)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WQB API Automation")
    parser.add_argument("--formula", type=str, help="Formula to test")
    parser.add_argument("--settings", type=str, default="TOP3000|MARKET|0|0.05",
                        help="Settings string: UNIVERSE|NEUTRALIZATION|DECAY|TRUNCATION")
    parser.add_argument("--auto-submit", action="store_true", help="Auto submit if IS passes")
    args = parser.parse_args()

    config = load_config()
    auto = WQBAutomation(config)
    auto.start()
    if auto.login():
        if args.formula:
            res = auto.submit_alpha(args.formula, args.settings, auto_submit=args.auto_submit)
            print(json.dumps(res, indent=2))
        else:
            print("Login successful. Run with --formula to test an alpha.")
    auto.stop()
