# Knowledge Gaps & Recommended Papers for Hermes/DeerFlow

## Current Knowledge Base (Đã có)

### 1. Research Papers (3 files)
- ✅ `research_papers/formulaic/101_formulaic_alphas.pdf` — Classic 101 formulaic alphas
- ✅ `research_papers/ml/alpha2.pdf`
- ✅ `research_papers/ml/autoalpha.pdf`

### 2. WorldQuant Official Docs (4 files)
- ✅ `wq_official/worldquant_brain_overview.md`
- ✅ `wq_official/competition_rules.md`
- ✅ `wq_official/alpha_lifecycle_guide.md`
- ✅ `wq_official/operator_reference.md`
- ✅ `wq_official/data_fields_catalog.json`

### 3. Reference Playbooks (3 files)
- ✅ `research_feeds/reference/agent_reading_pack_2026-05-18.md`
- ✅ `research_feeds/reference/fitness_optimization_playbook_2026-05-18.md`
- ✅ `research_feeds/reference/worldquant_metric_playbook_2026-05-17.md`

### 4. Lessons Learned (đã có nhiều)
- ✅ `lessons_learned/what_works.md`
- ✅ `lessons_learned/what_fails.md`
- ✅ `lessons_learned/market_regime_notes.md`
- ✅ Hàng chục file failure_recovery + bruteforce

---

## Missing High-Value Knowledge (Cần bổ sung)

### A. Advanced Alpha Construction Techniques

| # | Paper / Topic | Priority | Status | Notes |
|---|---------------|----------|--------|-------|
| 1 | **"Alpha Decay and Signal Erosion"** – How alphas lose edge over time | HIGH | ❌ Missing | Critical for long-term fitness |
| 2 | **"Turnover-Constrained Alpha Design"** – Explicit turnover penalty in expression | HIGH | ❌ Missing | Directly impacts fitness |
| 3 | **"Cross-Sectional vs Time-Series Momentum"** – When to use which | MEDIUM | ❌ Missing | Regime-aware generation |
| 4 | **"Volatility-Adjusted Ranking"** – Using realized vol as denominator | MEDIUM | ❌ Missing | Improves Sharpe stability |
| 5 | **"Multi-Horizon Ensemble"** – Combine 5d + 20d + 60d signals | MEDIUM | ❌ Missing | Better fitness in mixed regimes |

### B. Market Regime & Macro Context

| # | Paper / Topic | Priority | Status | Notes |
|---|---------------|----------|--------|-------|
| 6 | **"Regime-Dependent Alpha Performance"** – Bull/Bear/High-Vol regimes | HIGH | ❌ Missing | Current KB only has basic market_regime_notes |
| 7 | **"VIX and Alpha Robustness"** – How alphas behave in high VIX | MEDIUM | ❌ Missing | Useful for drawdown control |
| 8 | **"Sector Rotation Signals"** – Using sector ETF relative strength | LOW | ❌ Missing | Can improve neutralization |

### C. Operator & Expression Engineering

| # | Topic | Priority | Status | Notes |
|---|-------|----------|--------|-------|
| 9 | **"Safe vs Risky Operators"** – Which operators survive live trading | HIGH | ❌ Missing | Current operator_reference is just syntax |
| 10 | **"Expression Complexity vs Overfitting"** – When to stop adding operators | MEDIUM | ❌ Missing | Helps reduce self-correlation |
| 11 | **"Rank vs Zscore vs Raw"** – When to apply each transformation | MEDIUM | ❌ Missing | Frequently appears in good alphas |

### D. Recent Academic / Industry Papers (2024-2026)

| # | Paper | Priority | Status | Notes |
|---|-------|----------|--------|-------|
| 12 | **"LLM-based Alpha Mining"** – Papers on using LLMs for factor discovery | HIGH | ❌ Missing | Directly relevant to our system |
| 13 | **"Reinforcement Learning for Formulaic Alpha"** – AlphaGen / HARLA style | MEDIUM | ❌ Missing | Good for future hybrid generation |
| 14 | **"Evolutionary Prompt Optimization for Quant Strategies"** – AlphaEvolve style | MEDIUM | ❌ Missing | Can improve Hermes prompt quality |

---

## Recommended Action Plan

### Phase 1 – Immediate (Add 5 high-impact docs)
1. Create `lessons_learned/turnover_optimization.md`
2. Create `lessons_learned/regime_aware_alpha.md`
3. Add paper summary: "Alpha Decay and Signal Erosion"
4. Add paper summary: "Turnover-Constrained Alpha Design"
5. Add paper summary: "Safe vs Risky Operators in Live Trading"

### Phase 2 – Medium Term
- Add 3-4 recent LLM/RL alpha mining papers
- Build "Regime Detection Playbook" from daily research feeds
- Create operator risk matrix (which operators cause high turnover / low robustness)

### Phase 3 – Long Term
- Implement automated daily paper scraping + summarization into `research_feeds/daily/`
- Add "Alpha Aging Analysis" based on historical performance_log

---

**File created:** `knowledge_base/knowledge_gaps.md`  
**Last updated:** 2026-05-19
