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

# Go to simulate
page.goto("https://platform.worldquantbrain.com/simulate", wait_until="domcontentloaded")
page.wait_for_timeout(5000)

# Check page state BEFORE setting formula
state_before = page.evaluate('''() => {
    // ALTCHA
    const altcha = document.querySelector('altcha-widget');
    const altchaState = altcha?.shadowRoot?.querySelector('.altcha')?.getAttribute('data-state');
    // Simulate button
    const simBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Simulate');
    const btnInfo = simBtn ? {
        disabled: simBtn.disabled,
        classes: simBtn.className,
        hasDisabledClass: simBtn.className.includes('disabled'),
        ariaDisabled: simBtn.getAttribute('aria-disabled')
    } : null;
    // Textarea
    const ta = document.querySelector('textarea[aria-roledescription="editor"]');
    return {
        altcha: altchaState,
        button: btnInfo,
        hasTextarea: !!ta,
        textareaValue: ta ? ta.value : null
    };
}''')
print(f"Before formula:", flush=True)
for k, v in state_before.items():
    print(f"  {k}: {v}", flush=True)

# Set formula via keyboard typing (more realistic than JS setter)
page.click('textarea[aria-roledescription="editor"]')
page.wait_for_timeout(500)
page.keyboard.type("-rank(ts_delta(close, 5))", delay=30)
page.wait_for_timeout(2000)

# Check page state AFTER formula
state_after = page.evaluate('''() => {
    const simBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Simulate');
    const ta = document.querySelector('textarea[aria-roledescription="editor"]');
    return {
        button: simBtn ? {
            disabled: simBtn.disabled,
            classes: simBtn.className,
            hasDisabledClass: simBtn.className.includes('disabled')
        } : null,
        textareaValue: ta ? ta.value : null
    };
}''')
print(f"\nAfter formula:", flush=True)
for k, v in state_after.items():
    print(f"  {k}: {v}", flush=True)

# Click simulate anyway (forced)
page.evaluate('''() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Simulate');
    if (btn) {
        btn.disabled = false;  // Force enable
        btn.click();
        return 'clicked';
    }
    return 'not_found';
}''')
print("Force clicked simulate (disabled=false)", flush=True)

# Wait for changes
for i in range(12):
    page.wait_for_timeout(5000)
    html = page.content()
    if "experiencing" in html:
        print(f"[{i*5}s] Server error!", flush=True)
        break
    if "Sharpe" in html:
        print(f"[{i*5}s] Results found!", flush=True)
        break
    print(f"[{i*5}s] Waiting... ({len(html)} chars)", flush=True)

page.screenshot(path="wqb_logs/debug_simulate_final.png")
browser.close()
p.stop()
print("Done", flush=True)
