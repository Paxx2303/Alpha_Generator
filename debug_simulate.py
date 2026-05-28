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
        print(f"Login -> {page.url}", flush=True)
        break

# Navigate to simulate (in case we're on tutorial)
page.goto("https://platform.worldquantbrain.com/simulate", wait_until="domcontentloaded")
page.wait_for_timeout(3000)
print(f"On page: {page.url}", flush=True)

# Wait for editor
for i in range(20):
    editor = page.locator('.monaco-editor')
    if editor.is_visible(timeout=1000):
        print(f"Editor ready (attempt {i+1})", flush=True)
        break
    page.wait_for_timeout(1000)

# Set formula
page.evaluate('''(formula) => {
    const textarea = document.querySelector('textarea[aria-roledescription="editor"]');
    if (textarea) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        setter.call(textarea, formula);
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }
}''', "-rank(ts_delta(close, 5))")
print("Formula set", flush=True)
page.wait_for_timeout(1000)

# Click Simulate via JS
clicked = page.evaluate('''() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
        if (b.textContent.trim() === 'Simulate') {
            console.log('Found simulate button:', b.className);
            b.click();
            return b.className;
        }
    }
    return 'not_found';
}''')
print(f"Simulate click: {clicked}", flush=True)

# Wait and check for changes
for i in range(12):
    page.wait_for_timeout(5000)
    page.screenshot(path=f"wqb_logs/debug_{i}.png")
    html = page.content()
    
    # Check for error
    if "experiencing" in html:
        print(f"[{i*5}s] Server error detected!", flush=True)
        break
    
    # Check for results
    if "Sharpe" in html:
        print(f"[{i*5}s] Results found!", flush=True)
        # Find Sharpe
        import re
        sharpe = re.search(r'Sharpe[:\s]*(-?[\d.]+)', html)
        if sharpe:
            print(f"  Sharpe: {sharpe.group(1)}", flush=True)
        break
    
    print(f"[{i*5}s] Waiting... (page size: {len(html)} chars)", flush=True)

browser.close()
p.stop()
print("Done", flush=True)
