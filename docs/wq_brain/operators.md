# WorldQuant Brain - Operator Reference

Source: https://platform.worldquantbrain.com/learn/operators

This file is the authoritative operator catalog ingested by `WQBrainDocsRAG`
(see `knowledge_base/wq_docs_rag.py`) and by `LLMGenerator` when building
prompts for Hermes / DeerFlow / OpenRouter. Keep entries terse and accurate so
they can be retrieved verbatim into prompts.

Conventions used below:

- `x`, `y` are vector (cross-sectional) expressions: one value per instrument
  per day, unless specified otherwise.
- `d`, `lookback`, `window` are positive integer lookback windows expressed in
  trading days. Allowed lookbacks in this project: `5`, `10`, `20`, `60`
  (hard limit enforced by `LLMGenerator` MANDATORY RULES).
- `g` is a group expression (e.g. `subindustry`, `industry`, `sector`,
  `market`, `country`).
- All operators are pure, deterministic functions of their inputs at the
  current cross-section / time slice.

---

## 1. Arithmetic operators

Elementwise math on cross-sections. Safe for use anywhere.

- `add(x, y)` -> `x + y`. Also written as `x + y`.
- `subtract(x, y)` -> `x - y`. Also `x - y`.
- `multiply(x, y)` -> `x * y`. Also `x * y`.
- `divide(x, y)` -> `x / y`. NaN where `y == 0`.
- `power(x, y)` -> `x ** y`.
- `abs(x)` -> absolute value.
- `sign(x)` -> -1, 0, or +1.
- `log(x)` -> natural log, NaN where `x <= 0`.
- `exp(x)` -> exponential.
- `sqrt(x)` -> square root, NaN where `x < 0`.
- `inverse(x)` -> `1 / x`.
- `min(x, y)`, `max(x, y)` -> elementwise min/max.
- `signed_power(x, y)` -> `sign(x) * (abs(x) ** y)`.
- `s_log_1p(x)` -> `sign(x) * log(1 + abs(x))`. Variance-stabilizing log.

## 2. Logical operators

Return 1.0 / 0.0 (NaN on missing). Useful for conditional alphas and masks.

- `less(x, y)`, `greater(x, y)`, `equal(x, y)`, `not_equal(x, y)`
- `less_equal(x, y)`, `greater_equal(x, y)`
- `and(x, y)`, `or(x, y)`, `not(x)`
- `if_else(cond, x, y)` -> `x` where `cond != 0`, else `y`.

## 3. Cross-sectional operators

Operate across all instruments on the same date. Output is one number per
instrument.

- `rank(x)` -> per-day cross-sectional rank, scaled to `[0, 1]`. NaNs are
  dropped before ranking.
- `rank(x, rate=2)` -> tied-aware ranking variant.
- `zscore(x)` -> `(x - mean(x)) / std(x)` across the cross-section.
- `scale(x, scale=1)` -> rescale so `sum(abs(x)) == scale` per day.
- `normalize(x, useStd=true, limit=0.0)` -> demean (and optionally rescale).
- `quantile(x, driver="gaussian")` -> map ranks to a chosen distribution.
- `winsorize(x, std=4)` -> clip cross-section to +-`std` standard deviations.
- `truncate(x, maxPercent=0.01)` -> clip each weight to at most `maxPercent`
  of book on the long and short side.
- `vector_neut(x, y)` -> neutralize `x` against `y` cross-sectionally
  (linear projection).
- `regression_neut(x, y)` -> residual of OLS `x ~ y` per day.
- `pareto(x, alpha=1.0)` -> Pareto tail transform.

## 4. Time-series operators

Operate over a rolling window of `d` trading days for each instrument
independently. These are the bread-and-butter of WorldQuant alphas.

- `ts_mean(x, d)` -> rolling mean over the last `d` days.
- `ts_sum(x, d)` -> rolling sum.
- `ts_std_dev(x, d)` -> rolling sample standard deviation.
- `ts_var(x, d)` -> rolling variance.
- `ts_median(x, d)` -> rolling median.
- `ts_min(x, d)`, `ts_max(x, d)` -> rolling min / max.
- `ts_arg_min(x, d)`, `ts_arg_max(x, d)` -> index (0..d-1) of the rolling
  min / max.
- `ts_delta(x, d)` -> `x - ts_delay(x, d)`.
- `ts_delay(x, d)` -> value `d` days ago.
- `ts_returns(x, d)` -> `(x / ts_delay(x, d)) - 1`.
- `ts_rank(x, d)` -> rank of today's `x` within its trailing `d`-day window,
  scaled to `[0, 1]`.
- `ts_zscore(x, d)` -> `(x - ts_mean(x,d)) / ts_std_dev(x,d)`.
- `ts_scale(x, d)` -> rescale to `[0, 1]` over the trailing window.
- `ts_corr(x, y, d)` -> Pearson correlation between `x` and `y` over `d`.
- `ts_covariance(x, y, d)` -> rolling covariance.
- `ts_co_skewness(x, y, d)`, `ts_co_kurtosis(x, y, d)` -> higher-order
  co-moments.
- `ts_skewness(x, d)`, `ts_kurtosis(x, d)` -> rolling shape stats.
- `ts_decay_linear(x, d)` -> linearly weighted average where the most recent
  day has the highest weight.
- `ts_decay_exp_window(x, d, factor=0.5)` -> exponentially weighted average.
- `ts_product(x, d)` -> rolling product.
- `ts_count_nans(x, d)` -> count of NaNs in the last `d` days.
- `hump(x, hump=0.01)` -> smooth a signal by only updating when change
  exceeds `hump`. Reduces turnover.
- `jump_decay(x, d, sensitivity=0.5)` -> decay-style smoother with jump
  protection.

## 5. Group operators

Aggregate or normalize across a grouping `g` (e.g. `subindustry`,
`industry`, `sector`, `market`, `country`).

- `group_mean(x, weight, g)` -> weighted mean of `x` within each group.
- `group_neutralize(x, g)` -> demean `x` within each group (sets weighted
  group sum to zero). Standard sector / industry neutralization.
- `group_rank(x, g)` -> rank within group, scaled to `[0, 1]`.
- `group_zscore(x, g)` -> z-score within group.
- `group_normalize(x, g)` -> rescale within group.
- `group_scale(x, g)` -> rescale weights within group.
- `group_sum(x, g)`, `group_count(x, g)`, `group_max(x, g)`,
  `group_min(x, g)`, `group_median(x, g)`, `group_std_dev(x, g)`.
- `group_percentage(x, g, percentage=0.5)` -> percentile within group.
- `group_backfill(x, g, d, std=4.0)` -> fill NaNs using the group's last
  valid observation within `d` days.

## 6. Transformational operators

Shape an alpha for turnover, capacity, and weight distribution constraints.

- `trade_when(trigger, alpha, exit)` -> only take the alpha when `trigger`
  is true; flatten when `exit` is true. Lets you build event-driven alphas
  while controlling turnover.
- `pasteurize(x)` -> remove cross-sectional outliers / NaNs.
- `densify(x)` -> propagate sparse signals to nearby instruments using the
  cross-section.
- `clamp(x, low, high)` -> clip to `[low, high]`.

## 7. Vector operators

Operate on vector-valued inputs (multi-dimensional fields such as analyst
estimates, news tags, options surfaces).

- `vec_avg(x)`, `vec_sum(x)`, `vec_count(x)` -> reductions across the vector
  dimension.
- `vec_max(x)`, `vec_min(x)`, `vec_argmax(x)`, `vec_argmin(x)`.
- `vec_choose(x, nth=0)` -> pick the n-th component.
- `vec_norm(x)` -> Euclidean norm.

---

## Usage rules enforced by this project

When generating new alphas, prompts MUST respect:

1. Use only operators from this catalog. Never invent operator names
   (e.g. `rank1`, `ts_log_returns`, `mean_rev` are NOT operators).
2. Lookbacks `d` must be one of `5, 10, 20, 60`. Other windows are rejected
   by the validator and the project's quality gate.
3. Cross-sectional ops (`rank`, `zscore`, `scale`) should wrap raw fields
   before they are combined with other cross-sections, to avoid scale
   mismatches.
4. Use `ts_*` ops for any temporal aggregation. Do not roll your own mean.
5. For neutralization prefer `group_neutralize(x, subindustry)` or rely on
   the `neutralization=SUBINDUSTRY` simulate parameter set by
   `LLMGenerator`.
6. To control turnover, wrap signals with `ts_decay_linear`,
   `ts_decay_exp_window`, `hump`, or `trade_when` rather than tightening
   thresholds blindly.
7. Always include at least one volume-related component (`volume`,
   `vwap`, `adv20`, `ts_corr(close, volume, d)`, etc.) unless the strategy
   is pure price-momentum.

Anything outside this list is non-portable and should not be emitted.
