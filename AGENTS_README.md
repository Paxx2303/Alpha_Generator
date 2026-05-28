# Agent Reference — Alpha Generator

Detailed specification of system architecture, data flow, variables, and known issues.
This file is optimized for AI agents reading the codebase.

---

## 1. File Map

| File | Purpose | Entry Points | Dependencies |
|---|---|---|---|
| `wqb_automation.py` | Playwright-based WQB browser automation | `WQBAutomation.__init__()`, `.start()`, `.login()`, `.submit_alpha()`, `.stop()` | `playwright`, `wqb_config.json` or env vars |
| `alpha_agent.py` | Autonomous research loop: research → hypothesis → submit → analyze → improve | `main()` with `--quick`, `--headless`, `--max-cycles` | `wqb_automation.py`, `alpha_skills/Skill.md` |
| `run_pipeline.py` | CLI for stock screening pipeline | CLI args: `--universe`, `--top-n`, `--start`, `--end`, `--tickers`, `--no-cache` | `stock_pipeline/` |
| `stock_pipeline/__init__.py` | Package exports | `create_pipeline()`, `run_pipeline()` | `stock_pipeline/*.py` |
| `stock_pipeline/data_fetcher.py` | `DataFetcher` class | `DataFetcher.__init__(use_cache, cache_dir)`, `.fetch_data(tickers, start, end)` | `yfinance` |
| `stock_pipeline/alpha_factors.py` | `AlphaFactorEngine` class | `AlphaFactorEngine.__init__()`, `.compute_all(df)`, `.get_factor(name)` | 18 factor methods |
| `stock_pipeline/screener.py` | `StockScreener` class | `StockScreener.__init__(factors, weights)`, `.screen(df, universe_size, top_n)` | `AlphaFactorEngine` |
| `stock_pipeline/config.py` | Default config variables | `DEFAULT_UNIVERSE`, `DEFAULT_TOP_N`, `FACTOR_WEIGHTS` | — |
| `alpha_skills/Skill.md` | Knowledge base: themes, operators, settings, IQC, automation guide | Read by AI agent | — |
| `wqb_config.json` | WQB credentials (gitignored) | Loaded by `load_config()` | — |

---

## 2. WQBAutomation — Variables & Constants

### File: `wqb_automation.py`

#### Class: `WQBAutomation`

| Variable | Type | Default | Description |
|---|---|---|---|
| `self.config` | dict | from `load_config()` | `email`, `password`, `url`, `headless`, `timeout_ms` |
| `self.browser` | Browser or None | None | Playwright Chromium instance |
| `self.context` | BrowserContext or None | None | Browser context with viewport 1920x1080 |
| `self.page` | Page or None | None | Active page |
| `self.results_log` | list[dict] | [] | History of all simulation results this session |

#### `load_config()` → dict

Read order:
1. Environment variables: `WQB_EMAIL`, `WQB_PASSWORD`, `WQB_URL`, `WQB_HEADLESS`, `WQB_TIMEOUT`
2. JSON file: `wqb_config.json` in project root
3. Falls: `RuntimeError`

#### `login()` → bool

Flow:
1. Navigate to `{url}/sign-in`
2. Wait for email/password fields to render
3. Fill credentials (CSS: `input[name="email"]`, `input[name="password"]`)
4. Wait 2000ms for ALTCHA auto-verification (`altcha-widget` shadow DOM, triggers automatically)
5. Submit via `form.requestSubmit()` — this is the **only working method** (prev: button click was intercepted by React disabled state)
6. Wait up to 20s for URL redirect away from `/sign-in`
7. Handle tutorial redirect: if redirected to `/simulate/tutorial` or `/simulate/learn/courses`, dismiss intro.js overlay

Known issues:
- ALTCHA is a custom element with shadow DOM, `data-state="verified"` indicates solved
- Login redirect is inconsistent: can go to `/simulate`, `/simulate/tutorial`, or `/simulate/learn/courses`
- `form.requestSubmit()` triggers React form handler properly; `btn.click()` does NOT work because React controls button disabled state

#### `submit_alpha(formula, settings_str)` → dict

Parameters:
- `formula` (str): WQ Brain formula syntax (e.g. `"-rank(ts_delta(close,5))"`)
- `settings_str` (str): `"Universe|Neutralization|Decay|Truncation"` (default: `"TOP3000|Market|0|0.05"`)

Flow:
1. Ensure on simulate page (navigate if on `/learn/` sub-path)
2. Dismiss intro.js overlay (5 attempts, click skip button or JS remove)
3. Wait for Monaco editor render (up to 20s polling every 1s)
4. Set formula text via `nativeInputValueSetter` on textarea + dispatch `input` event
5. Save screenshot + page HTML for debugging
6. Dismiss cookie consent banner (`cky-btn-accept`)
7. Click Simulate button via:
   - **Try 1**: Playwright `click(force=True)` on `button.editor-simulate-button-text`
   - **Try 2**: JS `dispatchEvent(new MouseEvent('click', ...))` on `button` with text "Simulate"
   - **Try 3**: Focus `textarea[aria-roledescription="editor"]` → press `Control+Enter`
8. Click "Results" checkbox (`code-checkbox__label:has-text("Results")`)
9. Wait up to 10 minutes (120 attempts × 5s) for results
10. Parse metrics from HTML via regex
11. Retrigger simulate every 5 attempts (2-9) if no progress detected
12. Log results to `wqb_logs/alpha_<timestamp>.json`

Return dict keys:
| Key | Type | Source |
|---|---|---|
| `sharpe` | float or None | Regex `Sharpe:\s*(-?[\d.]+)` |
| `fitness` | float or None | Regex `Fitness:\s*(-?[\d.]+)` |
| `turnover` | float or None | Regex `Turnover:\s*([\d.]+)%` |
| `returns` | float or None | Regex `Returns:\s*(-?[\d.]+)%` |
| `drawdown` | float or None | Regex `Drawdown:\s*([\d.]+)%` |
| `margin` | float or None | Regex `Margin:\s*(-?[\d.]+)` |
| `yearly` | list[dict] | Year-by-year table parsed from HTML |
| `formula` | str | Input formula |
| `settings` | str | Input settings |
| `timestamp` | str | ISO datetime |
| `error` | str | Only on timeout: `"Timeout waiting for simulation"` |

#### Known Bug — Simulate Error

Current behavior: Simulate button IS clicked (all 3 methods tried), but page shows "WorldQuant BRAIN is experiencing some difficulties." This error persists and no metrics are returned.

Root cause candidates:
- Formula might be invalid or rejected
- ALTCHA may need re-verification per simulation (not just login)
- Server-side rate limiting on the account
- Page may be in `/simulate/learn/courses` sub-state and simulate button doesn't trigger proper API call

Workaround attempts:
- Retrigger simulate every 5 attempts
- Tried Playwright force click, JS dispatch, and Ctrl+Enter
- All produce the same error

---

## 3. Alpha Agent — Flow & State

### File: `alpha_agent.py`

#### Main Loop

```
1. RESEARCH:
   - Read alpha_skills/Skill.md knowledge base
   - Check wqb_logs/gold_alphas.json for existing passes
   - Identify untested themes

2. HYPOTHESIS:
   - Pick a theme (Mean Reversion, Momentum, VWAP, Volatility, etc.)
   - Generate 3-5 formula variants with economic rationale
   - Choose best variant based on prior learnings

3. SUBMIT:
   - Call WQBAutomation.submit_alpha(formula, settings)
   - Wait for simulation results
   - Save to log

4. ANALYZE:
   - If Sharpe >= 1.25 + Fitness >= 1.0 → save to gold_alphas.json, optimize settings
   - If Sharpe < -0.5 → flip sign, resubmit
   - If Sharpe 0~0.5 → change field/lookback, resubmit
   - If Turnover > 70% → add decay, resubmit
   - If error/timeout → log failure, try next variant

5. LOOP:
   - Max cycles determined by --max-cycles (default 20)
   - Update Skill.md learnings after each cycle
   - Report summary to user
```

#### CLI Arguments

| Arg | Type | Default | Description |
|---|---|---|---|
| `--quick` | flag | False | Dry-run: research + hypothesis only, no submission |
| `--headless` | flag | False | Run Playwright in headless mode |
| `--max-cycles` | int | 20 | Max research → submit → analyze cycles |

---

## 4. Stock Pipeline — Internal Structure

### `stock_pipeline/data_fetcher.py`

```python
class DataFetcher:
    def __init__(self, use_cache=True, cache_dir="stock_data_cache"):
        # cache_dir: pathlib.Path, stores pickle files per ticker

    def fetch_data(self, tickers: list, start: str, end: str) -> dict:
        # Returns {ticker: pd.DataFrame} with columns:
        # open, high, low, close, volume, returns, vwap, adv20, dvol
        # Uses yfinance.download(tickers, start, end)
```

### `stock_pipeline/alpha_factors.py`

```python
class AlphaFactorEngine:
    def __init__(self):
        # Registers 18 factor methods

    def compute_all(self, data: dict) -> pd.DataFrame:
        # Input: {ticker: DataFrame}
        # Output: MultiIndex DataFrame (date x ticker) with 18 factor columns

    def get_factor(self, name: str) -> pd.Series:
        # Returns specific factor Series
```

18 Factors: `vol_weighted_mr`, `mean_reversion_5`, `mean_reversion_10`, `momentum_5`, `momentum_10`, `momentum_20`, `volume_price_5`, `vwap_deviation`, `vwap_deviation_normalized`, `volatility_20`, `volatility_reversal`, `high_low_midpoint`, `high_low_position`, `liquidity_volume_ratio`, `amihud_illiquidity`, `volume_surge`, `money_flow`, `combined_mr_momentum`.

### `stock_pipeline/screener.py`

```python
class StockScreener:
    def __init__(self, factors: AlphaFactorEngine, weights: dict):
        # weights: {factor_name: weight} (default: factor_config.FACTOR_WEIGHTS)

    def screen(self, df: pd.DataFrame, universe_size: int = 1000, top_n: int = 10) -> pd.DataFrame:
        # 1. Filter top universe_size by avg dvol
        # 2. Score = weighted sum of factor z-scores
        # 3. Rank by score
        # Returns DataFrame: date, ticker, rank, score, factor_details
```

---

## 5. Settings Grid Reference

```
Format: Universe | Neutralization | Decay | Truncation
Default: TOP3000 | Market | 0 | 0.05

Optimization order:
1. TOP3000 + Market    + Decay 0  + Truncation 0.05    (baseline)
2. TOP3000 + Market    + Decay 3  + Truncation 0.05
3. TOP3000 + Subind.   + Decay 0  + Truncation 0.05
4. TOP1000 + Subind.   + Decay 10 + Truncation 0.10
5. TOP500  + Subind.   + Decay 0  + Truncation 0.10    (highest Sharpe)
```

Universe: TOP200 | TOP500 | TOP1000 | TOP3000
Neutralization: None | Market | Sector | Industry | Subindustry
Decay: 0 | 3 | 5 | 10 | 20
Truncation: 0.01 | 0.03 | 0.05 | 0.10 | 0.20

---

## 6. Known Issues & Workarounds

| Issue | Symptom | Root Cause | Workaround |
|---|---|---|---|
| Login hangs after submit | URL stays on `/sign-in` | ALTCHA verification timing | `form.requestSubmit()` + 20s polling loop |
| Login redirect inconsistency | Goes to `/simulate/tutorial` or `/simulate/learn/courses` | React router state | Auto-dismiss tutorial, force nav to `/simulate` |
| Simulate button not clickable | "No simulate button found" | Cookie banner overlay | Dismiss `.cky-btn-accept` first |
| Simulation shows error | "experiencing some difficulties" | Unknown (server-side) | No fix yet — retry with different formulas |
| Formula not typed | "No text input found" | Monaco editor not rendered | Wait loop up to 20s for `.monaco-editor` |
| CookieYes banner persistent | Overlays Simulate button | Loaded after React app | Click accept/reject before simulating |
| Captcha expired | Login success but simulate fails | ALTCHA token TTL | Short session — submit alpha immediately after login |

---

## 7. Log Files Directory Structure

```
wqb_logs/
├── alpha_<timestamp>.json         # Individual alpha results
├── gold_alphas.json               # Passed alphas (Sharpe >= 1.25 + Fitness >= 1.0)
├── after_login.png                # Screenshot after successful login
├── formula_entered.png            # Screenshot after filling formula
├── simulate_page.png              # Screenshot of simulate page
├── page_after_formula.html        # Full HTML dump after formula entry
├── page_debug.html                # Full HTML dump when error occurs
├── no_button_debug.html           # Full HTML when simulate button not found
├── wait_start.png                 # Screenshot at start of wait loop
├── sim_check_<N>.png              # Periodic screenshots during simulation wait
├── login_page.png                 # Screenshot of login page
├── login_failed.png               # Screenshot on login failure
└── tutorial_page.png              # Screenshot of tutorial redirect
```

---

## 8. Monaco Editor Interaction

WQB uses Monaco Editor (VS Code's editor). Standard textarea methods don't work because React wraps the editor.

Working approach:
```javascript
const textarea = document.querySelector('textarea[aria-roledescription="editor"]');
const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, 'value'
).set;
nativeInputValueSetter.call(textarea, formula);
textarea.dispatchEvent(new Event('input', { bubbles: true }));
```

This bypasses React's synthetic event system and triggers Monaco's internal change detection.

---

## 9. ALTCHA Anti-Bot System

WQB uses ALTCHA widget (similar to reCAPTCHA) on sign-in page.
- Custom element: `altcha-widget`
- Challenge URL: `https://api.worldquantbrain.com/captcha`
- States: `unverified` → `verifying` → `verified`
- Auto-verifies after page load + email/password interaction
- Shadow DOM — cannot access via standard Playwright selectors
- Works automatically: Playwright's real browser environment passes the verification
- No manual interaction needed — just wait 2s after filling credentials
