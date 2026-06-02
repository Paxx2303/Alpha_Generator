# Agent Reference — Alpha Generator

Detailed specification of system architecture, data flow, variables, and known issues.
This file is optimized for AI agents reading the codebase.

---

## 1. File Map

| File | Purpose | Entry Points | Dependencies |
|---|---|---|---|
| `wqb_automation/__init__.py` | Package exports | `WQBAutomation` | — |
| `wqb_automation/config.py` | WQB credentials config | `WQBConfig.load()` | `wqb_config.json` or env vars |
| `wqb_automation/selectors.py` | CSS selectors & locators | `Selectors` class | — |
| `wqb_automation/browser.py` | Browser lifecycle management | `BrowserManager` class | Playwright |
| `wqb_automation/login_handler.py` | Login flow & ALTCHA handling | `LoginHandler.login()` | Playwright |
| `wqb_automation/simulate_handler.py` | Alpha submission & result parsing | `SimulateHandler.submit()` | Playwright |
| `wqb_automation/knowledge_base.py` | Skill reading & updating | `KnowledgeBase` class | `alpha_skills/Skill.md` |
| `alpha_agent.py` | Autonomous research loop with skill evolution | `main()` with `--quick`, `--headless`, `--max-cycles` | `wqb_automation/`, `alpha_skills/Skill.md` |
| `run_pipeline.py` | CLI for stock screening pipeline | CLI args: `--universe`, `--top-n`, `--start`, `--end`, `--tickers`, `--no-cache` | `stock_pipeline/` |
| `stock_pipeline/__init__.py` | Package exports | — | `stock_pipeline/*.py` |
| `stock_pipeline/data_fetcher.py` | `DataFetcher` class | `DataFetcher.__init__()`, `.fetch_batch()` | `yfinance` |
| `stock_pipeline/alpha_factors.py` | `AlphaFactorEngine` class | `.compute_all()`, `.compute_factor()` | Factor methods |
| `stock_pipeline/stock_screener.py` | `StockScreener` class | `.rank_stocks()`, `.get_top_stocks()` | Factor data |
| `stock_pipeline/pipeline.py` | `StockPipeline` orchestration | `.run()` | All stock_pipeline modules |
| `alpha_skills/Skill.md` | Knowledge base: themes, operators, settings, IQC, automation guide | Read/written by agent | — |
| `wqb_config.json` | WQB credentials (gitignored) | Loaded by `WQBConfig.load()` | — |

---

## 2. Automation Module Structure

### `wqb_automation/config.py`

```python
@dataclass
class WQBConfig:
    email: str
    password: str
    url: str = "https://platform.worldquantbrain.com"
    headless: bool = False
    timeout_ms: int = 300000

    @classmethod
    def load() -> WQBConfig  # Env vars override file
```

### `wqb_automation/selectors.py`

CSS selectors as constants for maintainability:
- `Selectors.LOGIN_PAGE`, `Selectors.PASSWORD_INPUT`, `Selectors.SIGNIN_FORM`
- `Selectors.MONACO_EDITOR`, `Selectors.TEXTAREA_EDITOR`
- `Selectors.SIMULATE_BUTTON`, `Selectors.RESULTS_CHECKBOX`
- `Selectors.COOKIE_BANNER_ACCEPT/REJECT`, `Selectors.TUTORIAL_CLOSE_BUTTONS`

### `wqb_automation/browser.py`

```python
class BrowserManager:
    browser: Browser
    context: BrowserContext
    page: Page

    def start() -> BrowserManager
    def stop()
    def navigate(url, wait_until="domcontentloaded")
    def screenshot(name)
```

### `wqb_automation/login_handler.py`

```python
class LoginHandler:
    def __init__(browser_manager: BrowserManager, config: WQBConfig)

    def login() -> bool:
        # 1. Navigate to /sign-in
        # 2. Dismiss cookie banner
        # 3. Fill email/password
        # 4. Wait for ALTCHA auto-verification (2s)
        # 5. Submit via form.requestSubmit()
        # 6. Wait for redirect (20s polling)
        # 7. Handle tutorial redirect
```

### `wqb_automation/simulate_handler.py`

```python
class SimulateHandler:
    def __init__(browser_manager: BrowserManager, kb: KnowledgeBase)

    def submit(formula: str, settings_str: str) -> dict:
        # 1. Navigate to /simulate
        # 2. Dismiss overlays (cookie + intro.js)
        # 3. Find & type formula in editor
        # 4. Click Simulate (fallback 3 methods)
        # 5. Click Results checkbox
        # 6. Wait & parse metrics (up to 10 min)
        # 7. Save log

    def parse_metrics(html: str) -> dict:
        # Extract Sharpe, Fitness, Turnover, Returns, Drawdown, Margin, Yearly

    def run_settings_grid(formula: str, entry: dict) -> list:
        # Test formula across SETTINGS_GRID
```

### `wqb_automation/knowledge_base.py`

```python
class KnowledgeBase:
    def read() -> dict:
        # Load themes, patterns, operators from Skill.md

    def update_learning(formula: str, result: dict, diagnosis: dict) -> None:
        # Append new finding to Skill.md

    def get_gold_alphas() -> list:
        # Load passed alphas from wqb_logs/gold_alphas.json

    def save_gold(formula: str, settings: dict, result: dict) -> None:
        # Save passing alpha to gold_alphas.json
```

---

## 3. Alpha Agent — Flow & State

### File: `alpha_agent.py`

#### Main Loop (with Skill Evolution)

```
1. RESEARCH (before each alpha):
   - Read alpha_skills/Skill.md knowledge base
   - Load existing gold_alphas.json for pattern matching
   - Identify under-tested themes

2. HYPOTHESIS GENERATION:
   - Select theme based on learning gaps
   - Generate formula variants with economic rationale
   - Weight against known failures

3. SUBMIT TO WQB:
   - Login if session expired
   - Submit formula + settings
   - Wait for simulation

4. ANALYZE RESULTS:
   - Parse Sharpe, Fitness, Turnover, Yearly
   - Diagnose issues (sign, turnover, stability)
   - If PASS (Sharpe≥1.25 + Fitness≥1.0) → save to gold
   - If FAIL → generate fix suggestions

5. UPDATE SKILL KNOWLEDGE BASE:
   - Write results to Skill.md learnings section
   - Record successful patterns
   - Note failed patterns for avoidance
   - Update theme effectiveness scores

6. LOOP:
   - Max cycles via --max-cycles (default 20)
   - Exit early on gold alpha found
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
    cache_dir: Path
    use_cache: bool

    def fetch_ticker(ticker, start, end) -> Optional[pd.DataFrame]
    def fetch_batch(tickers, start, end) -> pd.DataFrame  # Parallel via ThreadPoolExecutor
```

### `stock_pipeline/alpha_factors.py`

```python
class AlphaFactorEngine:
    factor_registry: Dict[str, callable]

    def compute_factor(name, df) -> pd.Series
    def compute_all(df) -> pd.DataFrame

    # Factors: vol_weighted_mr, mean_reversion_5/10, momentum_5/10/20,
    # volume_price_5, vwap_deviation, vwap_deviation_normalized,
    # volatility_20, volatility_reversal, high_low_midpoint, high_low_position,
    # liquidity_volume_ratio, amihud_illiquidity, volume_surge, money_flow, combined_mr_momentum
```

### `stock_pipeline/stock_screener.py`

```python
class StockScreener:
    config: StockPipelineConfig
    factor_weights: dict

    def filter_universe(factor_df, date, universe) -> pd.DataFrame
    def compute_composite_score(factor_df, weights) -> pd.Series
    def rank_stocks(factor_df, date) -> pd.DataFrame
    def get_top_stocks(factor_df, date, top_n) -> pd.DataFrame
    def generate_report(factor_df, dates) -> dict
```

---

## 5. Settings Grid Reference

```
Format: Universe | Neutralization | Decay | Truncation
Default: TOP3000 | Market | 0 | 0.05

Optimization order:
1. TOP3000 + Market + Decay 0 + Truncation 0.05  (baseline)
2. TOP3000 + Market + Decay 5 + Truncation 0.05  (reduce turnover)
3. TOP3000 + Subind. + Decay 0 + Truncation 0.05 (increase Sharpe)
4. TOP1000 + Subind. + Decay 10 + Truncation 0.10 (optimize Fitness)
5. TOP500 + Subind. + Decay 0 + Truncation 0.10 (maximize Sharpe)
```

Universe: TOP200 | TOP500 | TOP1000 | TOP3000
Neutralization: None | Market | Sector | Industry | Subindustry
Decay: 0 | 3 | 5 | 10 | 20
Truncation: 0.01 | 0.03 | 0.05 | 0.10 | 0.20

---

## 6. Known Issues & Workarounds

| Issue | Symptom | Root Cause | Workaround |
|---|---|---|---|
| Login hangs after submit | URL stays on `/sign-in` | ALTCHA timing | `form.requestSubmit()` + 20s polling |
| Login redirect inconsistency | Goes to `/simulate/tutorial` | React router state | Auto-dismiss tutorial, nav to `/simulate` |
| Simulate button blocked | Button not clickable | Cookie banner overlay | Dismiss `.cky-btn-accept` first |
| Simulation error | "experiencing some difficulties" | Server-side / ALTCHA | Retry with different formula |
| Monaco editor not ready | "No text input found" | Editor lazy load | Wait loop up to 20s for `.monaco-editor` |
| Captcha expired | Login success but simulate fails | ALTCHA token TTL | Submit alpha immediately after login |

---

## 7. Log Files Directory

```
wqb_logs/
├── alpha_<timestamp>.json            # Individual simulation results
├── gold_alphas.json                  # Passed alphas (Sharpe≥1.25 + Fitness≥1.0)
├── knowledge_update_<timestamp>.json # Skill evolution log
├── after_login.png                   # Login success screenshot
├── formula_entered.png               # Formula entry screenshot
├── simulate_page.png                 # Simulate page state
├── page_debug.html                   # Full HTML on errors
└── sim_check_<N>.png               # Periodic simulation screenshots
```

---

## 8. Result Parsing Patterns

```python
# Extract metrics from simulation results HTML
patterns = {
    "sharpe": r'Sharpe[:\\s]*(-?[\\d.]+)',
    "fitness": r'Fitness[:\\s]*(-?[\\d.]+)',
    "turnover": r'Turnover[:\\s]*([\\d.]+)%',
    "returns": r'Returns[:\\s]*(-?[\\d.]+)%',
    "drawdown": r'Drawdown[:\\s]*([\\d.]+)%',
    "margin": r'Margin[:\\s]*(-?[\\d.]+)',
}
```

---

## 9. Skill Evolution Format

Skill.md updated after each alpha with:

```markdown
## Learnings

### Pattern: <theme>
- **Best Formula**: <formula string>
- **Sharpe**: <value>
- **Notes**: <diagnosis insights>

### Failed Patterns
- Formula: <formula> → Issue: <diagnosis>

### Settings Optimization
- Best: <settings> → Sharpe: <value>
```