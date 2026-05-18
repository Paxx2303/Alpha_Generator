# Mean Reversion Alpha

## When to use
Use when short-term reversals dominate and turnover stays manageable.

## Good patterns
- `rank(-ts_delta(close, 5))`
- `rank(-(close / ts_mean(close, 20) - 1))`

