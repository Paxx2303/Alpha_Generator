import sys
print("Starting playwright test...", flush=True)

from playwright.sync_api import sync_playwright
print("Import OK", flush=True)

p = sync_playwright().start()
print("Playwright started", flush=True)

browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
print("Browser launched", flush=True)

page = browser.new_page()
page.goto("https://platform.worldquantbrain.com/sign-in", wait_until="domcontentloaded", timeout=30000)
print(f"Page loaded: {page.url}", flush=True)

browser.close()
p.stop()
print("Done", flush=True)
