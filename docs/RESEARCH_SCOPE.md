# Research Scope: WQB → General Quant

## Current Scope (v3): WorldQuant Brain (WQB)

The system is currently scoped to **WorldQuant Brain** as the alpha testing platform.

### WQB Constraints
- **Universe:** USA equity (TOP1000, TOP3000)
- **Formula language:** WQB expression language (not Python/R)
- **Broken operators:** `ts_max`, `ts_min`, `delay` — do not use
- **Pass criteria:** Sharpe ≥ 1.25, Fitness ≥ 1.0, Turnover 10–70%
- **Settings format:** `UNIVERSE|NEUTRALIZATION|DECAY|TRUNCATION`

### Proven Signal Families (as of June 2026)
| Family | Best Sharpe | Notes |
|--------|-------------|-------|
| Fundamental Corr Divergence | 1.79 | `-ts_corr(eps_est, fcf_est, 20)` family |
| Earnings Yield Momentum | 1.70 | `ts_rank(eps/close, 60)` |
| EV/CF Zscore | 1.45 | Classic value |
| Intraday Reversal | 1.56 | High turnover, needs tuning |

---

## Near-Term Extensions (v3.1)

### More WQB Data Coverage
- Explore `anl4_*` (analyst estimate) fields more systematically
- Test `short_interest_ratio` and related fields
- Explore sector-specific formulas (tech vs industrials)

### Better Source Coverage
- Add SSRN paper crawler for q-fin working papers
- Add QuantConnect community forum crawler
- Add factor zoo tracker (systematic survey of documented anomalies)

---

## Long-Term Scope: General Quant Research

When accumulated WQB knowledge reaches saturation (< 2 new gold alphas per 10 cycles),
expand scope to general quantitative research:

### Alternative Platforms
- **Quantopian archives** (historical alphas, community strategies)
- **QuantConnect** (live paper trading environment)
- **Interactive Brokers paper account** (real execution testing)

### Research Domains Beyond WQB
| Domain | Description | Status |
|--------|-------------|--------|
| Factor investing | Fama-French extensions, quality factors | Partially covered |
| Alternative data | Satellite, credit card, web traffic signals | Future |
| Options flow | Put/call ratios as equity signals | Future |
| Macro regime | Interest rate regimes + equity factor rotation | Future |
| ML-based alphas | Gradient boosting on factor zoo | Future (needs compute) |

### Infrastructure Changes Needed for General Quant
1. Add `source_domain = "general_quant"` sources (already supported in schema)
2. Add platform-agnostic backtesting (Zipline/Backtrader)
3. Add a `platform` field to `alpha_results` table
4. DeerFlow skill: add "Translate WQB → platform X" workflow step

---

## Knowledge Source Roadmap

| Priority | Source | Domain | Why |
|----------|--------|--------|-----|
| P0 | WQB docs + mcp_skill.md | wqb_specific | Core knowledge already loaded |
| P0 | Legacy formulas (legacy_sources.md) | wqb_specific | 8 proven alphas to build on |
| P1 | arxiv q-fin (recent 2y) | general_quant | Academic edge discovery |
| P1 | SSRN factor zoo papers | general_quant | Comprehensive factor coverage |
| P2 | QuantConnect community | general_quant | Practitioner-tested ideas |
| P2 | WQB community forum | wqb_specific | Platform-specific tricks |
| P3 | Investment bank research | general_quant | Macro + sector views |
