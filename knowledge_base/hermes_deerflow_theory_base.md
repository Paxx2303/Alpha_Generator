# Hermes & DeerFlow Theoretical Knowledge Base (Updated 2026-05-19)

## 1. Core Papers & Concepts (MUST LEARN)

### 1.1 101 Formulaic Alphas (Kakushadze 2015) — ✅ Already in KB
- **Key Finding**: Returns strongly correlated with volatility (scaling ~0.76), **no significant dependence on turnover**
- **Implication**: High turnover does NOT necessarily kill alpha if volatility is controlled
- **Best Practice**: Focus on volatility-normalized expressions rather than blindly reducing turnover

### 1.2 Trading Volume Alpha (NBER 2024) — ❌ NEW
- **Core Idea**: Volume contains predictive information beyond price
- **Expression Pattern**: `rank(ts_corr(volume, returns, N))` or volume-confirmed reversals
- **Regime Note**: Volume alpha stronger in high-liquidity regimes, weaker in low-volume days

### 1.3 AlphaForge: Dynamic Factor Combination (arXiv 2024) — ❌ NEW
- **Key Innovation**: Re-rank factors daily using recent IC/IR performance
- **Dynamic Weighting**: Instead of fixed weights, re-fit linear model every day on last N days
- **Lesson for Hermes**: Generate alphas that are robust to factor rotation, not just static formulas

### 1.4 LLM-Powered MCTS for Alpha Mining (arXiv 2025) — ❌ NEW
- **Framework**: LLM + Monte Carlo Tree Search with backtesting feedback
- **Frequent Subtree Avoidance**: Prevent repetitive expression patterns
- **Direct Lesson**: Hermes should avoid generating near-duplicate formulas (self-correlation control)

---

## 2. High-Impact Concepts for Generation & Evaluation

### A. Turnover Optimization (Multiple Sources)
| Source | Finding | Action for Hermes/DeerFlow |
|--------|---------|---------------------------|
| Kakushadze 2015 | No direct turnover-return correlation | Do NOT sacrifice signal strength just to lower turnover |
| Medium article 2026 | Decay=4~10 reduces turnover while preserving signal | Prefer lookback 20-60 + decay 4-6 in prompts |
| AlphaForge 2024 | Dynamic re-ranking reduces effective turnover | Add "regime-adaptive" context in research prompt |

### B. Regime Awareness
- **Bull vs Bear**: Momentum works in bull, mean-reversion stronger in bear/high-vol
- **High VIX**: Volatility-normalized signals (divide by ts_std_dev) survive better
- **Action**: Add market regime summary (from daily research) into every generation prompt

### C. Operator Risk Matrix (Synthesize from multiple sources)
| Operator Family | Risk Level | Common Failure | Mitigation |
|-----------------|------------|----------------|------------|
| `abs()`, complex nesting | HIGH | Syntax error in local backtest | Avoid or wrap in rank |
| `ts_delta` with small N (1-5) | MEDIUM | High turnover, noise | Use N≥10 or combine with mean |
| `zscore` on short windows | MEDIUM | Unstable in low-liquidity | Prefer rank over zscore |
| Volume-price correlation | LOW-MEDIUM | Works only in liquid names | Good for TOP3000 |

---

## 3. Evaluation Criteria Upgrade (What Hermes/DeerFlow Should Check)

Current quality gate focuses on:
- Sharpe ≥ 1.5, Fitness ≥ 1.0, Turnover ≤ 0.7

**Add these theoretical checks** (in post-simulation review):

1. **Alpha Decay Resistance**
   - Does the expression use recent data only (high decay risk) or multi-horizon?
   - Prefer expressions with both short (5-10) and long (20-60) lookbacks

2. **Regime Robustness**
   - Test mentally: "Would this work in high VIX / low volume / earnings season?"
   - Penalize pure price-momentum in prompts when regime is "choppy"

3. **Economic Rationale**
   - Every alpha should have a one-sentence story (volume confirmation, over-reaction, liquidity provision, etc.)
   - DeerFlow review should enforce this

4. **Self-Correlation Awareness**
   - After generating, explicitly ask: "Is this too similar to recent approved alphas?"
   - Use knowledge_base/alpha_history to check motif repetition

---

## 4. Prompt Engineering Improvements for Hermes

### Current Prompt (too generic)
```
Generate {count} original WorldQuant FASTEXPR alpha expressions...
Research Context: {context}
```

### Recommended Enhanced Prompt
```
You are an expert quant researcher. Generate {count} novel FASTEXPR alphas for {strategy_type}.

MANDATORY RULES:
- Use only operators: ts_mean, ts_delta, ts_std_dev, ts_corr, rank, zscore, ts_rank
- Lookbacks: 5, 10, 20, 60 only
- Optimize for Fitness first (Sharpe × sqrt(|returns| / max(turnover,0.125)))
- Avoid near-duplicates of recently generated expressions
- Include at least one volume component unless strategy is pure momentum

CURRENT MARKET REGIME (from research):
{regime_summary}

RECENT SUCCESSFUL PATTERNS (from approved alphas):
{top_5_approved_motifs}

Return exactly one clean expression per line. No explanations.
```

---

## 5. DeerFlow Review Checklist (Post-Simulation)

Add these questions to DeerFlow's review prompt:

1. **Economic Story**: Does this alpha have a clear, testable hypothesis?
2. **Regime Fit**: Is the signal likely to survive current volatility/liquidity regime?
3. **Turnover Realism**: Given the operators and lookbacks, is the simulated turnover believable?
4. **Decay Risk**: Does the expression rely too heavily on very recent data (high decay)?
5. **Correlation Risk**: Does this motif already exist in the last 20 approved alphas?

---

## 6. Files to Create / Update

### New Files (High Priority)
```
knowledge_base/research_feeds/reference/
  - trading_volume_alpha_nber_2024.md          # NEW
  - alphaforge_dynamic_combination_2024.md     # NEW
  - llm_mcts_alpha_mining_2025.md              # NEW

knowledge_base/lessons_learned/
  - operator_risk_matrix.md                    # NEW
  - regime_aware_generation.md                 # NEW
```

### Update Existing
```
knowledge_base/lessons_learned/what_works.md
  → Add examples of high-fitness, low-decay alphas from 2025-2026

knowledge_base/research_feeds/daily/
  → Ensure every daily file contains "Regime Summary" section for prompt injection
```

---

**Last Updated:** 2026-05-19  
**Purpose:** Provide theoretical grounding for Hermes/DeerFlow to generate higher-quality, more robust alphas.
