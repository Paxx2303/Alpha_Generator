# Alpha Only Generation Pack - 20260518_072155

## Hermes

- rank(ts_mean(returns,5))
- rank(ts_mean(returns,10))
- rank(ts_mean(returns,20))
- rank(ts_mean(returns,60))
- rank(close / ts_mean(close,5) - 1)
- rank(close / ts_mean(close,20) - 1)
- rank(ts_delta(close,10) / ts_std_dev(close,10))
- rank(ts_delta(close,60) / ts_std_dev(close,60))
- rank(ts_corr(volume,returns,5))
- rank(ts_corr(volume,returns,20))
- rank(-ts_delta(close,10))
- rank(-ts_delta(vwap,60))

## DeerFlow

- rank(ts_mean(returns, 5))
- rank(ts_delta(close, 10) / ts_std_dev(close, 10))
- rank(close / ts_mean(close, 20) - 1)
- rank(ts_corr(volume, returns, 20))
- rank(volume / ts_mean(volume, 60))
- rank(-ts_delta(close, 60))
- rank(-ts_delta(vwap, 5))
- rank(ts_mean(returns, 20))
- rank(ts_delta(close, 5) / ts_std_dev(close, 5))
- rank(close / ts_mean(close, 60) - 1)
- rank(ts_corr(volume, returns, 60))
- rank(volume / ts_mean(volume, 20))

## Raw Summary

```json
{
  "hermes_count": 12,
  "deerflow_count": 12,
  "hermes_valid": 12,
  "deerflow_valid": 12
}
```
