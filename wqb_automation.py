"""
WorldQuant Brain Automation — Tu dong login, submit alpha, doc ket qua simulation.

Usage:
    python wqb_automation.py --formula "rank(ts_delta(close,5))" --settings "TOP3000|Market|0|0.05"
    python wqb_automation.py --file alpha.txt
    python wqb_automation.py --interactive
"""

import json
import os
import re
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


CONFIG_PATH = Path(__file__).parent / "wqb_config.json"
LOG_DIR = Path(__file__).parent / "wqb_logs"
LOG_DIR.mkdir(exist_ok=True)


def load_config():
    if "WQB_EMAIL" in os.environ:
        return {
            "email": os.environ["WQB_EMAIL"],
            "password": os.environ["WQB_PASSWORD"],
            "url": os.environ.get("WQB_URL", "https://platform.worldquantbrain.com"),
            "headless": os.environ.get("WQB_HEADLESS", "false").lower() == "true",
            "timeout_ms": int(os.environ.get("WQB_TIMEOUT", "300000")),
        }
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    raise RuntimeError(
        "No credentials found. Set WQB_EMAIL/WQB_PASSWORD env vars "
        "or create wqb_config.json"
    )


class WQBAutomation:
    def __init__(self, config: dict):
        self.config = config
        self.browser = None
        self.context = None
        self.page = None
        self.results_log = []

    def start(self):
        p = sync_playwright().start()
        self.browser = p.chromium.launch(
            headless=self.config["headless"],
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/129.0.0.0 Safari/537.36"
            ),
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.config["timeout_ms"])
        print("[WQB] Browser started")
        return self

    def stop(self):
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        print("[WQB] Browser closed")

    def login(self):
        print("[WQB] Logging in...")
        page = self.page
        base_url = self.config["url"]

        page.goto(f"{base_url}/sign-in", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        print(f"[WQB] Current URL: {page.url}")

        # Reject cookies to dismiss cookie banner
        for btn_text in ["Reject All", "Reject all", "Reject"]:
            try:
                btn = page.locator(f'button:has-text("{btn_text}")')
                if btn.is_visible(timeout=2000):
                    btn.click()
                    page.wait_for_timeout(1000)
                    print("[WQB] Cookies rejected")
                    break
            except Exception:
                pass

        page.screenshot(path=LOG_DIR / "login_page.png")

        # Fill email
        email_input = page.locator('input[type="email"]')
        email_input.wait_for(state="visible", timeout=10000)
        email_input.fill(self.config["email"])
        print("[WQB] Email filled")

        # Fill password (WQB uses name="currentPassword")
        pass_input = page.locator('input[name="currentPassword"], input[type="password"]').first
        pass_input.wait_for(state="visible", timeout=5000)
        pass_input.fill(self.config["password"])
        print("[WQB] Password filled")

        page.wait_for_timeout(1000)

        # Wait for ALTCHA auto-verification
        page.wait_for_timeout(2000)

        # Submit form via requestSubmit (works with React forms)
        result = page.evaluate('''() => {
            const form = document.querySelector('form');
            if (form && form.requestSubmit) {
                form.requestSubmit();
                return 'form_requestSubmit';
            }
            return 'no_form';
        }''')
        print(f"[WQB] Login submitted: {result}")

        # Wait for redirect (up to 20 seconds)
        for i in range(20):
            page.wait_for_timeout(1000)
            current = page.url.lower()
            if "/sign-in" not in current:
                print(f"[WQB] Redirected to: {current}")
                break

        page.wait_for_timeout(2000)
        print(f"[WQB] After login URL: {page.url}")
        page.screenshot(path=LOG_DIR / "after_login.png")
        print(f"[WQB] After login URL: {page.url}")

        # Check if login succeeded (URL changed from /sign-in)
        current = page.url.lower()
        logged_in = "/sign-in" not in current

        if logged_in:
            print(f"[WQB] Login SUCCESS -> {current}")
            # If redirected to tutorial, handle it
            if "tutorial" in current:
                page.wait_for_timeout(3000)
                page.evaluate("""() => {
                    var els = document.querySelectorAll('[class*="intro"], .introjs-overlay, .introjs-wrapper, .introjs-helperLayer');
                    for (var i = 0; i < els.length; i++) { els[i].remove(); }
                }""")
                page.wait_for_timeout(2000)
                page.screenshot(path=LOG_DIR / "tutorial_page.png")
                # Try to skip/dismiss tutorial
                for btn_text in ["Skip", "Done", "Close", "Got it"]:
                    try:
                        btn = page.locator(f'button:has-text("{btn_text}")')
                        if btn.is_visible(timeout=1000):
                            btn.click()
                            page.wait_for_timeout(1000)
                            print(f"[WQB] Tutorial dismissed: {btn_text}")
                            break
                    except:
                        pass
                page.wait_for_timeout(2000)
                print(f"[WQB] After tutorial: {page.url}")
        else:
            print("[WQB] Login FAILED - still on sign-in page")
            page.screenshot(path=LOG_DIR / "login_failed.png")
            raise RuntimeError("Login failed. Check credentials or wqb_logs/login_failed.png")

        return logged_in

    def submit_alpha(self, formula: str, settings_str: str = None):
        print(f"[WQB] Submitting alpha...")
        page = self.page
        base_url = self.config["url"]

        if settings_str is None:
            settings_str = "TOP3000|Market|0|0.05"

        # Always reload simulate page to ensure clean state
        page.goto(f"{base_url}/simulate", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        print(f"[WQB] Currently on: {page.url}")

        # Dismiss intro.js tutorial overlay
        page.evaluate("""() => {
            var els = document.querySelectorAll('[class*="intro"], .introjs-overlay, .introjs-wrapper, .introjs-helperLayer');
            for (var i = 0; i < els.length; i++) { els[i].remove(); }
        }""")
        # Dismiss cookie consent banner
        for btn_text in ["Reject All", "Reject all", "Reject", "Accept All"]:
            try:
                btn = page.locator(f'button:has-text("{btn_text}")')
                if btn.is_visible(timeout=1000):
                    btn.click()
                    page.wait_for_timeout(1000)
                    print(f"[WQB] Cookie banner dismissed: {btn_text}")
                    break
            except:
                pass

        page.screenshot(path=LOG_DIR / "simulate_page.png")

        # Wait for Monaco editor to appear
        formula_input = None
        # Debug: check what's on the page
        page.wait_for_timeout(5000)
        mc = page.evaluate('() => document.querySelectorAll(".monaco-editor").length')
        tc = page.evaluate('() => document.querySelectorAll("textarea").length')
        bc = page.evaluate('() => document.querySelectorAll("button").length')
        print(f"[WQB] Page elements: monaco={mc}, textarea={tc}, button={bc}")
        # Remove any overlays
        page.evaluate("""() => {
            var els = document.querySelectorAll('[class*="intro"], .introjs-overlay, .introjs-wrapper, .introjs-helperLayer, .cky-overlay, .cky-consent-container, .cky-modal');
            for (var i = 0; i < els.length; i++) { if(els[i].remove) els[i].remove(); }
        }""")
        # Try clicking where editor should be
        page.evaluate("""() => {
            var btns = document.querySelectorAll('a, button, div[role="button"]');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.includes('Create') || btns[i].textContent.includes('New Alpha')) {
                    btns[i].click(); break;
                }
            }
        }""")
        page.wait_for_timeout(3000)
        try:
            editor = page.locator('.monaco-editor')
            editor.wait_for(state="visible", timeout=30000)
            textarea = editor.locator('textarea')
            textarea.wait_for(state="visible", timeout=10000)
            formula_input = textarea.first
            print(f"[WQB] Monaco editor found")
        except Exception as e:
            print(f"[WQB] Editor not found: {e}")
            page.screenshot(path=LOG_DIR / "no_editor.png")
            with open(LOG_DIR / "no_editor.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            # Try any textarea as fallback
            try:
                formula_input = page.locator('.monaco-editor textarea').first
                if formula_input.count() > 0:
                    print(f"[WQB] Found textarea inside monaco-editor container")
            except:
                pass

        if formula_input is None:
            print("[WQB] No text input found. Saving page HTML for debugging...")
            with open(LOG_DIR / "page_debug.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            page.screenshot(path=LOG_DIR / "no_input_found.png")
            raise RuntimeError(
                "Cannot find formula input. Check wqb_logs/simulate_page.png "
                "and wqb_logs/page_debug.html"
            )

        # Type formula via keyboard (triggers Monaco validation correctly)
        try:
            ta = page.locator('textarea[aria-roledescription="editor"]').first
            ta.focus()
            page.wait_for_timeout(300)
            page.keyboard.press("Control+A")
            page.wait_for_timeout(100)
            page.keyboard.type(formula, delay=15)
            print("[WQB] Formula typed via keyboard")
        except Exception as e:
            print(f"[WQB] Keyboard type failed: {e}")
            try:
                page.evaluate('''(formula) => {
                    const ta = document.querySelector('textarea[aria-roledescription="editor"]');
                    if (ta) {
                        const setter = Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, 'value'
                        ).set;
                        setter.call(ta, formula);
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }''', formula)
                print("[WQB] Formula set via JS fallback")
            except Exception as e2:
                print(f"[WQB] All formula entry failed: {e2}")

        # Wait for Simulate button to become enabled (validation)
        print("[WQB] Waiting for formula validation...")
        for i in range(20):
            page.wait_for_timeout(500)
            r = page.evaluate('''() => {
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent.trim() === 'Simulate');
                if (!btn) return 'no_btn';
                return btn.disabled === false ? 'enabled' : 'disabled';
            }''')
            if r == 'enabled':
                print(f"[WQB] Simulate button enabled (attempt {i+1})")
                break
        else:
            print("[WQB] Simulate button still disabled — will force-enable")

        page.wait_for_timeout(1000)
        page.screenshot(path=LOG_DIR / "formula_entered.png")
        with open(LOG_DIR / "page_after_formula.html", "w", encoding="utf-8") as f:
            f.write(page.content())

        # Dismiss cookie consent banner
        for sel in ['.cky-btn-accept', '.cky-btn-reject']:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=500):
                    btn.click()
                    page.wait_for_timeout(300)
                    print(f"[WQB] Cookie banner dismissed: {sel}")
                    break
            except:
                pass

        # Click Simulate — force enable + JS click
        r = page.evaluate('''() => {
            const btn = Array.from(document.querySelectorAll('button'))
                .find(b => b.textContent.trim() === 'Simulate');
            if (!btn) return 'not_found';
            btn.disabled = false;
            btn.click();
            return 'ok';
        }''')
        print(f"[WQB] Simulate clicked: {r}")

        page.wait_for_timeout(5000)

        # Click "Results" checkbox to show results panel
        try:
            results_cb = page.locator('.code-checkbox__label:has-text("Results")')
            if results_cb.is_visible(timeout=2000):
                results_cb.click()
                print("[WQB] Results checkbox clicked")
                page.wait_for_timeout(1000)
        except Exception:
            pass

        print("[WQB] Waiting for simulation results...")
        page.screenshot(path=LOG_DIR / "wait_start.png")

        for attempt in range(60):
            time.sleep(5)
            content = page.content()

            # Check for error messages — break early
            if "experiencing some difficulties" in content:
                print("[WQB] ⚠️ Server error detected — breaking early")
                page.screenshot(path=LOG_DIR / "server_error.png")
                return {"error": "Server error: BRAIN experiencing difficulties", "sharpe": None}

            if attempt < 5:
                page.screenshot(path=LOG_DIR / f"sim_check_{attempt}.png")

            # Check for errors
            error_els = page.locator('[class*="error"], [class*="Error"], [class*="alert"]')
            try:
                if error_els.count() > 0:
                    for i in range(error_els.count()):
                        txt = error_els.nth(i).text_content()
                        if txt and len(txt) > 5:
                            print(f"[WQB] Error on page: {txt[:200]}")
            except Exception:
                pass

            metrics = self._parse_metrics(content)
            if metrics.get("sharpe") is not None:
                print(f"[WQB] Simulation done at attempt {attempt+1}")
                metrics["formula"] = formula
                metrics["settings"] = settings_str
                metrics["timestamp"] = str(datetime.now())
                self.results_log.append(metrics)
                self._save_log(metrics)
                return metrics

            if (attempt + 1) % 12 == 0:
                print(f"[WQB] Still waiting... ({(attempt+1)*5}s)")

        page.screenshot(path=LOG_DIR / "timeout.png")
        return {"error": "Timeout waiting for simulation", "sharpe": None}

    def _parse_metrics(self, html: str):
        metrics = {}

        patterns = {
            "sharpe": r'Sharpe[:\s]*(-?[\d.]+)',
            "fitness": r'Fitness[:\s]*(-?[\d.]+)',
            "turnover": r'Turnover[:\s]*([\d.]+)%',
            "returns": r'Returns[:\s]*(-?[\d.]+)%',
            "drawdown": r'Drawdown[:\s]*([\d.]+)%',
            "margin": r'Margin[:\s]*(-?[\d.]+)',
        }

        for key, pat in patterns.items():
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                val = m.group(1).replace("%", "").replace("\u2031", "").strip()
                try:
                    metrics[key] = float(val)
                except ValueError:
                    metrics[key] = val

        # Yearly table - try multiple patterns
        yearly = re.findall(
            r'(\d{4})\s+(-?[\d.]+)\s+([\d.]+%?)\s+(-?[\d.]+)\s+(-?[\d.]+%?)',
            html
        )
        if not yearly:
            yearly = re.findall(
                r'(\d{4})\s+(-?[\d.]+)\s+([\d.]+%?)\s+(-?[\d.]+)',
                html
            )

        if yearly:
            metrics["yearly"] = [
                {
                    "year": int(y[0]),
                    "sharpe": float(y[1]),
                }
                for y in yearly if len(y) >= 2
            ]

        return metrics

    def _save_log(self, metrics: dict):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = LOG_DIR / f"alpha_{ts}.json"
        with open(log_path, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"[WQB] Log saved: {log_path}")

    def run_alpha_loop(self, formulas: list, settings_str: str = None):
        print(f"[WQB] Running {len(formulas)} alphas sequentially...")
        results = []
        for i, formula in enumerate(formulas):
            print(f"\n{'='*60}")
            print(f"[WQB] Alpha {i+1}/{len(formulas)}")
            print(f"{'='*60}")
            print(formula)
            print()

            result = self.submit_alpha(formula, settings_str)
            results.append(result)

            sharpe = result.get("sharpe")
            if sharpe is not None:
                print(f"  Sharpe: {sharpe:.2f} | Fitness: {result.get('fitness','N/A')}")
            else:
                print(f"  Error: {result.get('error', 'Unknown')}")

            self._print_comparison(results)

        return results

    def _print_comparison(self, results: list):
        print(f"\n--- Comparison ({len(results)} alphas) ---")
        print(f"{'#':<3} {'Sharpe':<8} {'Fitness':<8} {'Turnover':<10} {'Status'}")
        for i, r in enumerate(results):
            s = r.get("sharpe", "?")
            f = r.get("fitness", "?")
            t = r.get("turnover", "?")
            e = r.get("error", "OK")
            s_str = f"{s:.2f}" if isinstance(s, float) else str(s)
            f_str = f"{f:.2f}" if isinstance(f, float) else str(f)
            print(f"{i+1:<3} {s_str:<8} {f_str:<8} {str(t):<10} {e}")


def read_formula_file(path: str):
    with open(path) as f:
        content = f.read().strip()
    blocks = re.split(r'\n\s*\n', content)
    return [b.strip() for b in blocks if b.strip()]


def main():
    parser = argparse.ArgumentParser(description="WQB Alpha Automation")
    parser.add_argument("--formula", help="Alpha formula string")
    parser.add_argument("--file", help="File containing formula(s)")
    parser.add_argument(
        "--settings",
        default="TOP3000|Market|0|0.05",
        help="universe|neutralization|decay|truncation",
    )
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--interactive", action="store_true", help="Enter formulas manually")
    parser.add_argument("--debug", action="store_true", help="Debug mode - more screenshots")

    args = parser.parse_args()

    formulas = []
    if args.formula:
        formulas = [args.formula]
    if args.file:
        formulas = read_formula_file(args.file)
    if args.interactive:
        print("Enter formulas (end with empty line):")
        while True:
            line = sys.stdin.readline().strip()
            if not line:
                break
            formulas.append(line)

    if not formulas:
        print("No formulas provided. Use --formula, --file, or --interactive")
        sys.exit(1)

    config = load_config()
    if args.headless:
        config["headless"] = True

    auto = WQBAutomation(config)
    try:
        auto.start()
        logged_in = auto.login()
        if not logged_in and not args.debug:
            print("[WQB] Login check failed. Use --debug to investigate.")
        auto.run_alpha_loop(formulas, args.settings)
    except Exception as e:
        print(f"[WQB] Error: {e}")
    finally:
        auto.stop()


if __name__ == "__main__":
    main()
