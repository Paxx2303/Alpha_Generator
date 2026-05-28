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

page.goto("https://platform.worldquantbrain.com/simulate", wait_until="domcontentloaded")
page.wait_for_timeout(3000)

# Remove intro.js
page.evaluate("""() => {
    document.querySelectorAll('.introjs-overlay, [class*="intro-"]').forEach(el => el.remove());
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

# Wait for enable
for i in range(20):
    page.wait_for_timeout(500)
    r = page.evaluate('() => { const b = Array.from(document.querySelectorAll("button")).find(x => x.textContent.trim() === "Simulate"); return b ? !b.disabled : "no"; }')
    if r == True:
        print(f"Button enabled ({i+1})", flush=True)
        break

# Click simulate
page.evaluate('() => document.querySelector("button.editor-simulate-button-text")?.click()')
page.wait_for_timeout(2000)

# Click Results checkbox
page.evaluate('''() => {
    const labels = document.querySelectorAll('.code-checkbox__label');
    for (const l of labels) {
        if (l.textContent.trim() === 'Results') {
            l.click(); return;
        }
    }
}''')

# Wait and scrape results
for i in range(20):
    page.wait_for_timeout(3000)
    html = page.content()
    
    # Parse metrics
    metrics = {}
    patterns = {
        "sharpe": r'Sharpe[:\s]*(-?[\d.]+)',
        "fitness": r'Fitness[:\s]*(-?[\d.]+)',
        "turnover": r'Turnover[:\s]*([\d.]+)%',
        "returns": r'Returns[:\s]*(-?[\d.]+)%',
        "drawdown": r'Drawdown[:\s]*([\d.]+)%',
        "margin": r'Margin[:\s]*(-?[\d.]+)',
    }
    for k, pat in patterns.items():
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            val = m.group(1).replace('%', '').strip()
            try: metrics[k] = float(val)
            except: metrics[k] = val
    
    if "sharpe" in metrics or "experiencing" in html:
        if "sharpe" in metrics:
            print(f"\n=== RESULTS (attempt {i+1}) ===", flush=True)
            for k, v in metrics.items():
                print(f"  {k}: {v}", flush=True)
        if "experiencing" in html:
            print("Server error", flush=True)
        break
    
    print(f"[{i*3}s] waiting...", flush=True)

page.screenshot(path="wqb_logs/final_result.png")
browser.close()
p.stop()
print("Done", flush=True)
