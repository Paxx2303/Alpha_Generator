# Momentum Alpha

## When to use
Use for short-to-medium horizon price continuation research.

## Good patterns
- `rank(ts_mean(returns, 10))`
- `rank(close / ts_mean(close, 20) - 1)`

