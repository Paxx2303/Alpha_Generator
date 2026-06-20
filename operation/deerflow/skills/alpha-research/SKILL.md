# Alpha Research Skill

## Purpose
Research quantitative alpha signals for WorldQuant Brain (WQB) platform.
Target: Sharpe ≥ 1.25, Fitness ≥ 1.0, Turnover 10–70%, USA TOP3000.

## Workflow

1. **Load knowledge** — Call `alpha-wqb.get_skill_knowledge` to load operator rules and proven patterns.
2. **Search existing gold alphas** — Call `alpha-wqb.get_gold_alphas` to avoid duplicates (correlation > 0.7).
3. **Form hypothesis** — Search academic sources (arxiv, SSRN) for a quantitative signal theory.
4. **Verify fields** — Call `alpha-wqb.search_data_fields` to confirm field names exist on WQB.
5. **Translate to formula** — Convert hypothesis into WQB expression.
6. **Test** — Call `alpha-wqb.submit_alpha` with settings: `TOP3000|Subindustry|3|0.08`.
7. **Diagnose result** — If fail, call `alpha-wqb.diagnose_alpha` for fix recommendations.
8. **Record findings** — Call `alpha-wqb.save_theory` to persist the insight for future sessions.
9. **Iterate** — Call `alpha-wqb.mutate_formula` to explore variations of a passing formula.

## Constraints

- **NEVER use**: `ts_max`, `ts_min`, `delay` — these are broken on WQB
- **Fitness formula**: `Fitness = Sharpe × √(|Returns| / max(TO, 0.125))` — maximize this
- **Truncation**: Always add `truncate(signal, 0.08)` for fundamentals-based signals to cap outliers
- **Neutralization**: Use `group_neutralize(signal, subindustry)` for industry-specific alphas
- **Correlation limit**: Avoid correlation > 0.7 with existing gold alphas

## Proven Signal Families (from legacy research)

| Family | Core Idea | Best Settings |
|--------|-----------|---------------|
| Fundamental Corr Divergence | `-ts_corr(eps_est, fcf_est, 20)` | TOP3000 \| Market \| 3 \| 0.08 |
| Earnings Yield Momentum | `ts_rank(eps/close, 60)` in industry | TOP1000 \| Industry \| 3 \| 0.08 |
| EV/CF Zscore | `-ts_zscore(ev/cashflow_op, 63)` | TOP1000 \| Industry \| 3 \| 0.08 |
| Intraday Reversal | `-(close-open)/open` smoothed | TOP3000 \| Market \| 3 \| 0.05 |

## Source Priority

DeerFlow should prioritize sources with high historical effectiveness.
Call `alpha-wqb.get_gold_alphas` before each session to see which signal families work.

Focus areas for new hypothesis search:
- Cross-sectional anomalies (earnings quality, accruals, cashflow quality)
- Short-term reversals (overnight gaps, analyst estimate revisions)
- Institutional flow signals (short interest, insider activity)
