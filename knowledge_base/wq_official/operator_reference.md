# WorldQuant Operator Reference

## Core Time-Series Operators
- `ts_mean(x, d)`: average over rolling window `d`
- `ts_delta(x, d)`: difference between current value and value `d` periods ago
- `ts_std_dev(x, d)`: rolling standard deviation
- `ts_corr(x, y, d)`: rolling correlation between `x` and `y`

## Cross-Sectional Operators
- `rank(x)`: normalize cross-section by ordinal rank
- `zscore(x)`: standardize cross-section

## Common Data Fields
- `close`
- `vwap`
- `returns`
- `volume`

