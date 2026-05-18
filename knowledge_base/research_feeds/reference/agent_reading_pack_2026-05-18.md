# Agent Reading Pack - 2026-05-18

Purpose:
- Give Hermes and DeerFlow a higher-signal research pack than the raw RSS feed.
- Convert new WorldQuant and market-regime research into concrete alpha-design rules.

## WorldQuant Research Context

- WorldQuant Learn2Quant emphasizes five habits that matter for this system:
  alpha ideation, using different data categories, diversifying the alpha pool, managing risk, and applying advanced research techniques.
- WorldQuant BRAIN is explicitly framed as a real-time simulation platform with data, dashboards, and value-added measures. The workflow is not only "generate formula" but "build, test, compare, and improve."
- A March 18, 2026 WorldQuant article says BRAIN has about 375,000 users, 13,000 research consultants, and more than 200,000 data fields. This means crowding risk is real, and diversity matters.

## Metric Interpretation for Alpha Design

- Sharpe:
  treat as the first filter for consistency, not just raw return.
- Fitness:
  use as the main efficiency metric. A formula with okay Sharpe but weak Fitness is often too noisy or too expensive in turnover terms.
- Turnover:
  high turnover is often a design problem, not just a trading-cost problem. Short horizons, noisy volume signals, or low decay often cause this.
- Drawdown:
  large drawdown often means the alpha is too regime-dependent or too concentrated.
- Self-correlation:
  uniqueness matters. A decent but differentiated alpha can be more valuable than another crowded momentum clone.

## 2026 Market-Regime Insights

### 1. Momentum is state-dependent, not universal

- Recent literature continues to show that momentum can crash when liquidity conditions change or market rebounds begin.
- Static signal definitions are fragile. State-conditional or regime-aware momentum design is safer than one fixed ranking rule for every market state.

Implication for agents:
- Do not treat one momentum expression as universally valid.
- Prefer families that can be adjusted by horizon, decay, and neutralization.
- Test both short-horizon continuation and reversal-sensitive variants.

### 2. Liquidity is a structural driver

- New 2026 work argues that cross-sectional liquidity improvements can explain a large share of momentum returns.
- Another 2026 study on intramonth momentum points toward market plumbing and liquidity needs rather than pure investor belief as a major driver.

Implication for agents:
- Price-only momentum is incomplete.
- Price-volume interaction, liquidity improvement, and turnover-aware ranking should be explored.
- However, volume-only motifs are often crowded, so combine them with range, volatility, or price normalization.

### 3. Hidden mean reversion remains important

- Recent regime-aware allocation research still finds that short-run momentum often coexists with medium-term reversal pressure.
- That means a signal can look strong in a short window but become fragile if the market is near a reversal regime.

Implication for agents:
- Pair trend expressions with reversal diagnostics.
- Reward alpha families that keep drawdown controlled when momentum weakens.
- Use slower decay, stronger truncation, or stricter neutralization when reversal risk rises.

## Agentic Alpha-Mining Research

### Hubble (arXiv:2604.09601)

- Hubble constrains generation to interpretable operator trees instead of free-form code.
- It uses dual-channel RAG, family-aware selection, formula-similarity penalties, and structured family diagnostics.
- In its reported U.S. equity run, the best out-of-sample group was led by range, volatility, and trend families, not crowded volume-only motifs.

Implication for Hermes and DeerFlow:
- Prefer family-level search over isolated formula search.
- Penalize repeated near-duplicate formulas.
- Promote range and volatility families when volume-only ideas dominate.

### QuantaAlpha (arXiv:2602.07085)

- QuantaAlpha treats each mining run as a trajectory, then mutates weak steps and recombines strong steps.
- It enforces semantic consistency among hypothesis, expression, and executable code.
- It also constrains complexity and redundancy to reduce crowding and improve transfer robustness.

Implication for Hermes and DeerFlow:
- After failures, do not only "try another formula."
- Rewrite the reasoning chain:
  hypothesis -> operator family -> horizon -> risk controls -> simulation result.
- Reuse successful substructures, but do not copy the full formula blindly.

## Practical Rules For This System

1. Favor families, not one-offs.
Each batch should compare at least trend, range, volatility, and price-volume interaction families.

2. Penalize volume-only crowding.
If top formulas all rely on raw volume ratios or simple volume correlation, force exploration into range or volatility families.

3. Treat turnover as a design signal.
If turnover is too high, first increase decay, slightly tighten truncation, or extend lookback before abandoning the hypothesis.

4. Reward low self-correlation explicitly.
An alpha with slightly lower Sharpe but better uniqueness can still be valuable for submission strategy.

5. Use regime-aware prompts.
When recent failures cluster around drawdown or crash risk, ask for alpha variants that are robust to rebound or liquidity-stress regimes.

6. Preserve interpretable operator structure.
Safe, short, auditable formulas should be preferred over complex but fragile expressions.

## Prompt Hints For Hermes And DeerFlow

- Ask for family-level comparisons, not just a single best formula.
- Ask which parameter changed the behavior:
  lookback, decay, truncation, neutralization, or delay.
- Ask why a winner works in terms of liquidity, volatility, or regime state.
- Ask whether a candidate is likely crowded or differentiated.
- Ask what the failure implies:
  weak edge, too much turnover, regime mismatch, concentration, or correlation crowding.

## Sources

- WorldQuant Learn2Quant:
  https://www.worldquant.com/learn2quant/
- WorldQuant BRAIN:
  https://www.worldquant.com/brain/
- WorldQuant IQC / BRAIN update, March 18, 2026:
  https://www.worldquant.com/ideas/worldquants-international-quant-championship-returns-for-its-sixth-year-following-record-global-participation-in-2025/
- Community notes on metrics and settings:
  https://github.com/jglazar/notes/blob/main/quant_interview/alpha_ideas.md
- AQR, Understanding Momentum and Reversals:
  https://www.aqr.com/Insights/Research/Working-Paper/Understanding-Momentum-and-Reversals?aqrPDF=1
- QuantaAlpha:
  https://arxiv.org/abs/2602.07085
- Hubble:
  https://arxiv.org/abs/2604.09601
- Dynamic Factor Allocation via Momentum-Based Regime Switching:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6224058
- Momentum Returns and the Role of Liquidity Improvements:
  https://papers.ssrn.com/sol3/Delivery.cfm/6483840.pdf?abstractid=6483840&mirid=1&type=2
- Static signal definitions and momentum crash risk:
  https://www.sciencedirect.com/science/article/pii/S154461232600396X
- Generating Alpha: A Hybrid AI-Driven Trading System:
  https://arxiv.org/abs/2601.19504
