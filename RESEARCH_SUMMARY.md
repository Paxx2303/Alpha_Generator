# Alpha Research Summary — 2026-06-06

## 📊 Current Status

### Portfolio (gold_alphas.json)
- **Total alphas**: 5
- **Submitted successfully**: 3
- **Failed self-correlation**: 1 (correlation 0.706 with Vk8jzqqJ)
- **Unsubmitted (ready)**: 1 (alpha 9qRKPxx1 — Sharpe 1.56, Fitness 1.02)

### Portfolio Breakdown

| ID | Theme | Status | Sharpe | Fitness | TO |
|----|-------|--------|--------|---------|-----|
| Vk8jzqqJ | EPS Yield Momentum | ✅ SUBMITTED | 1.56 | 1.10 | 21.9% |
| 6XEvXKmG | EV/CF Valuation | ✅ SUBMITTED | 1.45 | 1.06 | 17.8% |
| rKWvzA3j | Est Correlation | ✅ SUBMITTED | 1.77 | 1.64 | 16.3% |
| 1YgQo3gJ | EPS Yield Momentum | ❌ SELF_CORR | 1.70 | 1.11 | 19.6% |
| 9qRKPxx1 | Intraday Open-Close | 🟡 READY | 1.56 | 1.02 | 57.5% |

---

## 🔬 Research Conducted Today

### Batch 1: VWAP-Weighted Return Patterns
**Script**: `_research_vwap_patterns.py`
**Status**: ⚠️ INCOMPLETE (timeout after alpha #1)

**Results**:
1. **VWAP Reversal Pure [5d]**: Sharpe 1.63, Fitness 0.80 ❌ FAIL
   - Issue: Fitness too low (need ≥1.0)
   - Root cause: Returns 14.1% / TO 57.8% = ratio 0.24 (need ≥0.40)

**Remaining alphas** (2-5) were NOT completed due to timeout.

### Batch 2: Sales/Revenue Growth (READY TO RUN)
**Script**: `_research_sales_growth.py`
**Status**: 📝 Created, not executed
**Theme**: Sales/Revenue growth momentum (NOT used in current portfolio)
**Variants**: 4 candidates

---

## 📚 Knowledge Base Update

### ✅ Completed: mcp_skill.md Enhancement

Added **2 new sections**:

1. **Section 9**: "Stop & Rethink After 3 Consecutive Failures"
   - Rule: After 3 consecutive fails → STOP and analyze root cause
   - Check wqb_data.db history
   - Review portfolio themes to avoid self-correlation
   - Search knowledge base for new inspiration
   - Change approach (price→fundamental, single→composite, short→medium term)
   - Only test 2-3 variants (not 5-7) to conserve daily limit

2. **Section 10**: "Research Workflow"
   - Phase 1: Research & Hypothesis (check portfolio, search KB, write hypothesis)
   - Phase 2: First Simulation (2-3 variants max)
   - Phase 3: Analyze Results (stop if all fail, optimize if close, submit if pass)
   - Phase 4: Post-Submit (handle self-correlation failures)

**File stats**:
- Old: 11 sections, ~11,671 chars
- New: **13 sections**, ~13,500 chars
- Added: Research workflow, stop-and-rethink rule

---

## 🎯 Next Steps

### Option A: Submit Existing Alpha (RECOMMENDED)
```bash
python submit_best_daily_alpha.py --submit
```
- Alpha 9qRKPxx1 (Intraday) already passes IQC
- Safe submission — no additional research needed

### Option B: Continue Research (Sales/Revenue Growth)
```bash
python _research_sales_growth.py
```
- Theme NOT in portfolio → low self-correlation risk
- 4 variants targeting Industry neutralization + Decay 3
- Expected: at least 1-2 should pass IQC

### Option C: Fix VWAP Pattern (if really want VWAP theme)
- Alpha #1 had Fitness 0.80 (close to 1.0)
- Could try: increase Decay to 3 or 5 to reduce TO from 57.8% → ~35-40%
- Or: change neutralization from Subindustry → Industry

---

## 🚨 Daily Simulation Limit

- **Limit**: 7 alphas/day
- **Used today**: ~2-3 (VWAP #1 + possibly #2 from timeout)
- **Remaining**: ~4-5 slots
- **Recommendation**: Run sales_growth (4 alphas) OR submit existing alpha

---

## 📖 Lessons Applied

From 102 historical simulations:
- ✅ Using proven settings (TOP3000|Industry|3|0.08)
- ✅ Avoiding broken operators (pasteurize, ts_min)
- ✅ Checking self-correlation before submit
- ✅ Targeting Returns/TO ≥ 0.40 for Fitness ≥ 1.0
- ✅ Testing 2-4 variants per theme (not 7+)
- ✅ Focusing on themes NOT in portfolio

---

## 💾 Files Created/Modified Today

**Created**:
- `_research_vwap_patterns.py` (5 variants, 1 tested)
- `_research_sales_growth.py` (4 variants, ready to run)
- `_check_data_quality.py` (data analysis tool)
- `RESEARCH_SUMMARY.md` (this file)

**Modified**:
- `mcp_skill.md` (+2 sections: research workflow, stop-and-rethink rule)

**No changes**:
- `gold_alphas.json` (still 5 alphas, no new additions)
- Pipeline files (data quality is OK, no re-filtering needed)

---

## 🔍 Data Quality Verdict

**Report**: 76% WQB-relevant, 1,324 chunks, 40,730 tokens
**Issue**: quality_score = 0 for all chunks (scoring bug)
**Decision**: ❌ NO RE-FILTERING NEEDED
**Reason**: Content quality is actually good (formulas, concepts, tips visible in samples)

---

**Generated**: 2026-06-06 09:52 UTC  
**Next review**: After running sales_growth research or submitting alpha 9qRKPxx1
