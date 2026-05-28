import sys; sys.stdout.reconfigure(line_buffering=True)
from playwright.sync_api import sync_playwright

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

# Go to simulate
page.goto("https://platform.worldquantbrain.com/simulate", wait_until="domcontentloaded")
page.wait_for_timeout(3000)

# Remove intro.js overlay
page.evaluate('''() => {
    document.querySelectorAll('.introjs-overlay, [class*="intro-"]').forEach(el => el.remove());
}''')
page.wait_for_timeout(1000)

# Wait for editor
for i in range(20):
    if page.locator('.monaco-editor').is_visible(timeout=1000):
        print(f"Editor ready ({i+1})", flush=True)
        break
    page.wait_for_timeout(1000)

# Type formula via keyboard
ta = page.locator('textarea[aria-roledescription="editor"]').first
ta.focus()
page.wait_for_timeout(300)
page.keyboard.press("Control+A")
page.wait_for_timeout(100)
page.keyboard.type("-rank(ts_delta(close, 5))", delay=15)

# Check button state immediately
r = page.evaluate('''() => {
    const btn = Array.from(document.querySelectorAll('button'))
        .find(b => b.textContent.trim() === 'Simulate');
    if (!btn) return 'no_btn';
    return {disabled: btn.disabled, classes: btn.className};
}''')
print(f"Button after typing: {r}", flush=True)

# Wait for enable
for i in range(20):
    page.wait_for_timeout(500)
    r2 = page.evaluate('''() => {
        const btn = Array.from(document.querySelectorAll('button'))
            .find(b => b.textContent.trim() === 'Simulate');
        if (!btn) return 'no_btn';
        return btn.disabled === false ? 'enabled' : 'disabled';
    }''')
    if r2 == 'enabled':
        print(f"Button enabled at attempt {i+1}", flush=True)
        break
else:
    print(f"Button never enabled, forcing...", flush=True)

# Force enable + click
page.evaluate('''() => {
    const btn = Array.from(document.querySelectorAll('button'))
        .find(b => b.textContent.trim() === 'Simulate');
    if (btn) {
        btn.disabled = false;
        btn.click();
    }
}''')
print("Simulate clicked", flush=True)

# Wait for results
for i in range(12):
    page.wait_for_timeout(5000)
    html = page.content()
    if "experiencing" in html:
        print(f"[{i*5}s] Server error", flush=True)
        break
    if "Sharpe" in html:
        print(f"[{i*5}s] RESULTS FOUND!", flush=True)
        import re
        m = re.search(r'Sharpe[:\s]*(-?[\d.]+)', html)
        if m: print(f"  Sharpe={m.group(1)}", flush=True)
        break
    print(f"[{i*5}s] waiting ({len(html)} chars)", flush=True)

page.screenshot(path="wqb_logs/simulate_final.png")
browser.close()
p.stop()
print("Done", flush=True)
