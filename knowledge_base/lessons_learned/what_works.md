# What Works

- Sector-neutral momentum expressions with `rank()` wrappers tend to be more stable.
- Volume-confirmed signals often improve conviction versus price-only rules.
- Fitness should be optimized directly, not inferred from Sharpe alone.
- If turnover is above `0.125`, reducing turnover can materially help fitness.
- If turnover is already near or below `0.125`, improving Sharpe and Returns matters more than lowering turnover further.
- `N=20` and `N=60` often give better fitness than very short windows for price-volume motifs.
- Alternative neutralization can improve fitness even when Sharpe falls slightly.


- rank(ts_delta(close, 20) / ts_std_dev(close, 20)) | status=approved | sharpe=1.93 | fitness=2.00

- rank(ts_corr(volume, returns, 5)) | status=approved | sharpe=2.21 | fitness=1.73
