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
| `mcp_server.py` | MCP Server exposing WQB tools | `search_knowledge_base`, `submit_alpha`, `diagnose_alpha` | `wqb_automation/`, `alpha_skills/` |
| `submit_single.py` | Utility script to submit an alpha formula directly | `main()` | `wqb_automation` |
| `run_pipeline.py` | CLI for stock screening pipeline | CLI args: `--universe`, `--top-n`, `--start`, `--end`, `--tickers`, `--no-cache` | `stock_pipeline/` |
| `stock_pipeline/__init__.py` | Package exports | — | `stock_pipeline/*.py` |
| `stock_pipeline/data_fetcher.py` | `DataFetcher` class | `DataFetcher.__init__()`, `.fetch_batch()` | `yfinance` |
| `stock_pipeline/alpha_factors.py` | `AlphaFactorEngine` class | `.compute_all()`, `.compute_factor()` | Factor methods |
| `stock_pipeline/stock_screener.py` | `StockScreener` class | `.rank_stocks()`, `.get_top_stocks()` | Factor data |
| `stock_pipeline/pipeline.py` | `StockPipeline` orchestration | `.run()` | All stock_pipeline modules |
| `mcp_skill.md` | Single Source of Truth for Knowledge Base | Read/written by agent and MCP | — |
| `alpha_skills/knowledge_retriever.py` | Semantic search over academic papers | `KnowledgeRetriever.search()` | JSON Datasets |
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
    def __init__(browser_manager: BrowserManager)

    def submit(formula: str, settings_str: str) -> dict:
        # 1. Navigate to /simulate
        # 2. Dismiss overlays (cookie + intro.js)
        # 3. Find & type formula in editor
        # 4. Click Simulate (fallback 3 methods)
        # 5. Click Results checkbox
        # 6. Wait & parse metrics (up to 10 min)
        # 7. Save log
```

---

## 3. Data Flow (MCP Architecture)

1. **Ideation**: AI reads `mcp_skill.md` for guidelines and calls `search_knowledge_base` to retrieve academic rationale from `alpha_skills/final_dataset/`.
2. **Creation**: AI generates a formula based on the rationale.
3. **Execution**: AI calls the MCP tool `submit_alpha`. The server utilizes `wqb_automation.py` to drive Playwright.
4. **Analysis**: AI receives the metrics back from `submit_alpha`. If metrics are bad, it can call `diagnose_alpha` to get recommendations.
5. **Evolution**: If an alpha passes IQC, it is saved to `wqb_logs/gold_alphas.json`. AI can call `list_gold_alphas` and `mutate_from_gold` to build upon past successes.

---

## 4. Known Issues & Maintenance

### Playwright Flakiness
- **Monaco Editor**: WQB uses Monaco, which intercepts regular `page.fill()`. `SimulateHandler` uses a robust sequence of `page.click()` + `page.keyboard.type()` as a workaround.
- **Login Redirects**: Sometimes the URL doesn't change immediately after login, requiring careful polling.
- **API Rate Limiting**: Sending too many API requests via MCP at once can trigger `504 Gateway Time-out`. Handle with retries.

### Updating Selectors
When WQB updates its UI, `wqb_automation/selectors.py` is the ONLY file that needs changing.