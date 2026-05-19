# Hermes & DeerFlow Theory Check Log — 2026-05-19

## 1. Current Workflow Analysis

### Generation Path (LLMGenerator → Hermes)
- ✅ Hermes is now available (`hermes.available() = True`)
- ✅ Prompt asks for "original FASTEXPR" without templates
- ❌ Prompt still lacks:
  - Regime summary injection
  - Recent approved motif avoidance
  - Explicit turnover/fitness optimization rule
  - Operator risk guidance

### Evaluation Path (Hermes/DeerFlow Reviews)
- ✅ Pre-simulation and post-simulation reviews exist
- ❌ Reviews do not yet check:
  - Economic rationale / hypothesis
  - Regime robustness
  - Alpha decay risk
  - Motif repetition vs recent alphas

### Sign-Flip Logic (New)
- ✅ When pre-backtest Sharpe < -1.25 AND Fitness < -1.0 → flip sign + direct simulate
- ✅ Good for rescuing strongly negative candidates

---

## 2. Theoretical Gaps Identified (After Web Research)

| Gap | Evidence from Literature | Impact on Current Alphas | Fix Priority |
|-----|--------------------------|--------------------------|--------------|
| **Volume as predictor** | NBER 2024 "Trading Volume Alpha" | Many alphas ignore volume → lower edge | HIGH |
| **Dynamic re-ranking** | AlphaForge 2024 | Static generation misses regime shifts | HIGH |
| **LLM + MCTS + feedback** | arXiv 2025 | Hermes generates without backtest-guided refinement loop | MEDIUM |
| **Alpha decay awareness** | Multiple papers 2024-2025 | Short-horizon alphas die fast | HIGH |
| **Turnover vs Fitness trade-off** | Medium 2026 + Kakushadze | Over-penalizing turnover or ignoring it | MEDIUM |

---

## 3. Recommended Theory Files for Hermes/DeerFlow

### Must-Read (Create These)
1. `knowledge_base/research_feeds/reference/trading_volume_alpha_nber_2024.md`
2. `knowledge_base/research_feeds/reference/alphaforge_dynamic_combination_2024.md`
3. `knowledge_base/research_feeds/reference/llm_mcts_alpha_mining_2025.md`
4. `knowledge_base/lessons_learned/operator_risk_matrix.md`
5. `knowledge_base/lessons_learned/regime_aware_generation.md`

### Already Available (Use More Aggressively)
- ✅ 101 Formulaic Alphas → inject volatility scaling rule
- ✅ Fitness Optimization Playbook → enforce Fitness-first ordering
- ✅ WorldQuant Metric Playbook → remind of exact Fitness formula

---

## 4. Concrete Improvements for Next Cycle

### A. Generation Prompt Upgrade
Add to every Hermes call:
```
CURRENT REGIME: {daily_research_regime_summary}
AVOID MOTIFS: {last_5_approved_expressions}
PREFER: volume-return correlation, volatility normalization, multi-horizon (5+20+60)
OPTIMIZE: Fitness = Sharpe * sqrt(|returns| / max(turnover, 0.125))
```

### B. DeerFlow Post-Sim Review Upgrade
Add 5 explicit questions:
1. Economic hypothesis?
2. Regime fit?
3. Decay risk?
4. Turnover realism?
5. Motif repetition?

### C. Knowledge Injection
- Load `hermes_deerflow_theory_base.md` into RAG context every run
- Force Hermes to cite at least one concept from the theory base in rationale

---

## 5. Expected Outcome After Fixes

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| % alphas with valid FASTEXPR syntax | ~60% | >90% |
| Average Sharpe of generated alphas | -0.4 ~ 0.2 | 0.3 ~ 0.8 |
| % passing pre-backtest | <10% | 25-35% |
| Self-correlation of new alphas | High (repetitive motifs) | Lower (motif diversity enforced) |

---

**Log generated:** 2026-05-19 00:19  
**Next Action:** Implement prompt + review upgrades + create 3-5 new theory reference files.
