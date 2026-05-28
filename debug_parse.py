import sys; sys.stdout.reconfigure(line_buffering=True)
from playwright.sync_api import sync_playwright
import re

email = "namnguyen230304@gmail.com"
password = "pax230304"

p = sync_playwright().start()
browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
page = browser.new_page(viewport={"width": 1920, "height": 1080})
page.set_default_timeout(60000)

# Login
page.goto("https://platform.worldquantbrain.com/sign-in", wait_until="domcontentloaded")
page.fill('input[type="email"]', email)
page.fill('input[name="currentPassword"]', password)
page.wait_for_timeout(3000)
page.evaluate('() => document.querySelector("form")?.requestSubmit()')
for i in range(20):
    page.wait_for_timeout(1000)
    if "/sign-in" not in page.url.lower():
        print(f"Login OK: {page.url}", flush=True)
        break

# Remove intro.js
page.evaluate("""() => {
    var els = document.querySelectorAll('.introjs-overlay, [class*="intro-"]');
    for (var i = 0; i < els.length; i++) { els[i].remove(); }
}""")
page.wait_for_timeout(1000)

# Wait for editor
for i in range(20):
    if page.locator('.monaco-editor').is_visible(timeout=1000): break
    page.wait_for_timeout(1000)

# Type formula
ta = page.locator('textarea[aria-roledescription="editor"]').first
ta.focus()
page.wait_for_timeout(300)
page.keyboard.press("Control+A")
page.wait_for_timeout(100)
page.keyboard.type("-rank(ts_delta(close, 5))", delay=15)

# Wait for button enable
for i in range(20):
    page.wait_for_timeout(500)
    r = page.evaluate('() => { var b = Array.from(document.querySelectorAll("button")).find(function(x) { return x.textContent.trim() === "Simulate"; }); return b ? !b.disabled : "no"; }')
    if r == True: print(f"Button enabled ({i+1})", flush=True); break

# Click simulate
page.evaluate('() => { var b = document.querySelector("button.editor-simulate-button-text"); if (b) { b.click(); return "ok"; } return "no"; }')
print("Simulate clicked", flush=True)

# Wait 8 seconds for simulation
page.wait_for_timeout(8000)

# Save HTML and check for results
html = page.content()
with open("wqb_logs/sim_result.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML saved ({len(html)} chars)", flush=True)

# Search for Sharpe in various forms
for term in ["Sharpe", "sharpe", "SHARPE"]:
    idx = html.find(term)
    if idx >= 0:
        print(f"Found '{term}' at index {idx}", flush=True)
        print(f"Context: {html[max(0,idx-50):idx+100]}", flush=True)

# Search for other metrics
for term in ["Fitness", "Return", "Turnover", "Drawdown", "1.94", "1.2"]:
    idx = html.find(term)
    if idx >= 0:
        print(f"Found '{term}' at index {idx}", flush=True)

# Also search in visible text portions
text_blocks = re.findall(r'>([^<]{5,200})<', html)
for tb in text_blocks:
    if any(kw in tb for kw in ["Sharpe", "Fitness", "Turnover", "Return"]):
        print(f"Visible text: {tb.strip()}", flush=True)

page.screenshot(path="wqb_logs/sim_result.png")
browser.close()
p.stop()
print("Done", flush=True)
