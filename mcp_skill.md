---
name: wqb-alpha-generator
description: Comprehensive skill and knowledge base for creating, optimizing, and submitting WorldQuant Brain alphas. Provides mathematical frameworks and optimization techniques for Turnover, Fitness, and Sharpe.
---

# Skill: wqb-alpha-generator

This skill provides a complete toolset and knowledge base for the AI agent to act as an expert Quant Researcher, automatically interacting with WorldQuant Brain (WQB).

## 1. Capabilities (MCP Tools)
1. **`search_data_fields(query, limit)`**: Search for valid data fields on WQB (e.g. "sales", "options", "sentiment") to use in formulas.
2. **`search_knowledge_base(query)`**: [NEW] Search the internal knowledge base (papers, templates, economic rationale) to build hypotheses. **ALWAYS** use this before generating new themes.
3. **`generate_hypothesis()`**: Get a curated trading theme (e.g., Statistical Arbitrage, Mean Reversion) and its base formula.
4. **`submit_alpha(formula, settings, dry_run)`**: Submit an alpha expression for simulation and get backtest results (Sharpe, Fitness, Turnover).
5. **`diagnose_alpha(metrics)`**: Analyze a weak alpha and get recommendations on how to fix it.
6. **`mutate_formula(formula, n)`**: Auto-generate `n` variations of your formula (changing lookbacks, operators, adding group neutralization).
7. **`get_gold_alphas()`**: Retrieve past successful formulas (Sharpe > 1.25, Fitness > 1.0) for inspiration.

## 2. Core Knowledge & Rules

**ULTIMATE AI GOAL:**
NEVER create basic, simple Alphas (e.g., just using `rank(-ts_delta(close, 5))`). You MUST always aim to create **Complex/Composite Alphas** by:
1. **Cross-sectional & Time-series Blending:** Use `group_rank`, `group_neutralize` with time-series operators.
2. **Diverse Data Exploration:** Use `search_data_fields` to combine Fundamental (`sales`, `pe`), Sentiment, or Alternative data. Always wrap fundamental fields with `ts_backfill()`.
3. **Signal Blending:** Add or multiply different signals (e.g., Fundamental + Momentum + Volatility).
4. **Knowledge Retrieval:** Use `search_knowledge_base` to ground your formulas in academic research.

**IQC Criteria (In-Sample Quality Criteria):**
- **Sharpe Ratio:** $\ge 1.25$
- **Fitness:** $\ge 1.0$
- **Turnover:** $10\% - 70\%$ (Ideal: $<30\%$)
- **Fitness Formula:** `Fitness = Sharpe * sqrt(|Returns| / max(Turnover, 0.125))`

### Valid Operators
- **Time Series:** `ts_corr`, `ts_covariance`, `ts_rank`, `ts_scale`, `ts_arg_max`, `ts_arg_min`, `ts_decay_linear`, `ts_mean`, `ts_std_dev`, `ts_delta`, `ts_delay`, `ts_zscore`, `ts_regression`, `ts_sum`, `ts_av_diff`, `ts_backfill`, `trade_when`, `pasteurize`
- **Cross-Sectional:** `rank`, `normalize`, `zscore`, `winsorize`, `scale`, `quantile`
- **Group:** `group_neutralize`, `group_rank`, `group_zscore`, `group_vector_neut`
- **BROKEN Operators (DO NOT USE):**
  - `ts_log_returns` $\to$ use `log(close / ts_delay(close, d))`
  - `ts_min` $\to$ use `ts_scale` or `-ts_arg_min`
  - `ts_max` $\to$ use `ts_scale` or `ts_arg_max`
  - `delay` $\to$ use `ts_delay`
  - `stddev` $\to$ use `ts_std_dev`
  - `correlation` $\to$ use `ts_corr`
  - `delta` $\to$ use `ts_delta`

### Advanced Optimization Techniques

| Problem | Diagnosis | Fix |
|---------|-----------|-----|
| **Sharpe > 4.0** | Look-Ahead Bias | Verify `Delay=1` and no `ts_delay(x, 0)` is used |
| **Sharpe < 0** | Signal inverted | Add `-` sign to entire formula |
| **Turnover > 50%** | Too much trading | Apply `ts_decay_linear(signal, 5-10)` or `trade_when` thresholds |
| **Good Sharpe, bad Fitness** | Turnover too low / Wrong neutralization | Decrease Decay to 0 OR change to Market neutralization |
| **High drawdown > 15%** | Position concentration | Reduce Truncation to 0.03 or 0.01 |

### Proven Settings (Settings Grid)

| Universe | Neutralization | Decay | Truncation | Expected Sharpe | Use Case |
|----------|----------------|-------|------------|-----------------|----------|
| TOP3000  | Market         | 0     | 0.05       | Baseline        | Price/Volume, Mean Reversion |
| TOP500   | Subindustry    | 0     | 0.10       | High Sharpe     | Fundamental, Idiosyncratic risk |
| TOP1000  | Subindustry    | 10    | 0.10       | High Fitness    | Slow signals, Sentiment |

**Key Insight:** Price-volume alphas should use **Market** neutralization, NOT Subindustry. Neutralizing price reversion by Market reduces Sharpe slightly but GREATLY increases Fitness.

## 4. Examples of High-Quality Composite Alphas

**Example 1: Vol-Normalized Mean Reversion + Volume Regime Filter**
*Rationale*: Instead of naive price mean reversion, we normalize the price drop by the stock's 20-day volatility. We only trade this signal when the trading volume surges (top 30% of the month) compared to its 20-day average.
*Metrics*: Sharpe 0.91, Fitness 0.34, Turnover 32.59%, Drawdown 7.54% (Failed IQC slightly but has excellent turnover/risk control).
```python
lookback = 5;
vol = ts_std_dev(returns, 20);
signal = -group_rank(ts_delta(close, lookback) / (vol + 0.001), subindustry);
regime = ts_rank(volume / adv20, 20) > 0.7;
trade_when(regime, signal, -1)
```
*Settings*: TOP1000 | Subindustry | Decay: 0 | Truncation: 0.05

## 5. Project Structure
- `mcp_skill.md`: The single source of truth for alpha generation knowledge.
- `mcp_server.py`: Exposes WQB tools to the AI agent.
- `wqb_automation.py`: Core REST API client for WQB.
- `alpha_agent.py`: Autonomous agent generating formulas based on knowledge base search.
- `alpha_skills/knowledge_retriever.py`: RAG module to search academic papers and references.
