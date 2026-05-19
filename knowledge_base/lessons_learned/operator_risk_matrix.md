# Operator Risk Matrix for FASTEXPR Generation

## Purpose
Help Hermes/DeerFlow avoid generating expressions that fail local backtest or produce unrealistic metrics.

## Risk Levels

### HIGH RISK (Avoid or heavily penalize)
| Operator | Problem | Example Failure |
|----------|---------|-----------------|
| `abs()` | Not supported in local backtest evaluator | Syntax error |
| Deep nested functions (4+ levels) | Overfitting, high self-correlation | Complex but fragile |
| `ts_delta(close, 1)` or `ts_delta(volume, 1)` | Extreme noise, unrealistic turnover | High turnover + low Sharpe |

### MEDIUM RISK (Use with caution)
| Operator | Recommendation |
|----------|----------------|
| `zscore` on short windows (<10) | Unstable in low-liquidity names |
| Pure price momentum with N=5 | High decay risk |
| No volume component | Lower edge in modern markets |

### LOW RISK (Preferred)
| Operator | Why Safe |
|----------|----------|
| `rank(...)` | Cross-sectional normalization, stable |
| `ts_mean` + `ts_std_dev` | Volatility normalization improves Sharpe |
| `ts_corr(volume, returns, N)` | Strong theoretical grounding (NBER 2024) |
| Lookback 20 or 60 | Better regime robustness |

## Generation Rule
> "Prefer rank + volatility normalization + volume interaction. Use zscore sparingly. Never use abs()."

**Last Updated:** 2026-05-19
