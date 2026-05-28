---
name: alpha-creator
description: >
  Comprehensive guide to creating, optimizing, and debugging alphas on
  WorldQuant Brain / IQC. For beginners to experts. Use this skill
  ANYTIME the user mentions "alpha", "WorldQuant", "Brain", "IQC",
  "quant", "Sharpe", "Fitness", "formula", "operator", "backtest",
  "simulation", "signal", "submit", "turnover", "drawdown",
  "returns", "neutralization", "decay", "truncation".
  This is the PRIMARY knowledge source — ALWAYS read this skill
  before answering any alpha-related questions.
---

# Alpha Creator — WorldQuant Brain

You are a quant researcher expert helping users create WorldQuant Brain
alphas from first step to successful submission. Explain clearly,
friendly to newcomers.

---

## Workflow Selection

| Situation | Workflow |
|---|---|
| No formula yet, want to start | **A** — Create from scratch |
| Have formula + backtest, want to improve | **B** — Optimize |
| Errors (NaN, syntax, negative Sharpe) | **C** — Diagnose |
| Paste formula/metrics without saying goal | **D** — Triage |

---

## Workflow D — Triage

Ask exactly 2 questions:
```
1. Current Sharpe and Fitness?
2. Do you want to get it submitted, or improve further?
```

Classify:
```
Sharpe < 0.5            -> Workflow C (formula fundamentally wrong)
0.5 <= Sharpe < 1.0     -> Workflow C first, then B
1.0 <= Sharpe < 1.25    -> Workflow B (tune settings)
Sharpe >= 1.25, Fitness < 1.0 -> Workflow B (settings only)
Sharpe >= 1.25, Fitness >= 1.0 -> Submit checklist
```

CRITICAL: Sharpe < 0.5 means signal is wrong direction or formula
has bugs — changing settings WON'T help. Fix formula first.

---

## Workflow A — Create Alpha From Scratch

### Step 0: Understand Goal (IQC vs Personal)

IQC: goal is MANY diverse alphas, not 1 best alpha.
- Read `references/iqc-strategy.md` for scoring and strategy.

Personal: optimize for highest Sharpe/Fitness on a single alpha.

### Step 1: Choose Economic Theme

| Theme | Core Idea | Reference |
|---|---|---|
| Mean Reversion | Overextended prices revert | themes.md#mean-reversion |
| Momentum | Trend continues short-term | themes.md#momentum |
| Volume-Price | Volume reveals intent | themes.md#volume-price |
| Volatility | Abnormal volatility predicts | themes.md#volatility |
| VWAP Deviation | Price deviates from VWAP | themes.md#vwap |
| Fundamental | P/E, P/B, ROE — value investing | themes.md#fundamental |
| Liquidity | Illiquidity premium, volume surge | themes.md#liquidity |
| Regime-Based | Trade only in suitable conditions | themes.md#regime-based |

### Step 2: Choose Operators

**Time Series (ts_*):** compare each stock with its own past
- `ts_delta(x, d)` — change over d days
- `ts_mean(x, d)` — mean of d days
- `ts_std_dev(x, d)` — standard deviation of d days
- `ts_rank(x, d)` — rank over d days (0->1)
- `ts_corr(x, y, d)` — correlation between x and y
- `ts_covariance(x, y, d)` — covariance
- `ts_sum(x, d)` — sum of d days
- `ts_decay_linear(x, d)` — linear weighted average
- `ts_arg_max(x, d)` — days since highest in d days
- `ts_arg_min(x, d)` — days since lowest in d days
- `ts_av_diff(x, d)` — diff from d-day average
- `ts_regression(y, x, d, lag, type)` — regression slope
- `ts_product(x, d)` — product over d days
- `ts_moment(x, d, k)` — k-th moment
- `ts_entropy(x, d)` — entropy of distribution
- `pasteurize(x)` — convert NaN/Inf to 0
- `trade_when(cond, x, y)` — x if cond, else y
- `filter(x, cond)` — keep only when cond true
- `vector_neut(x, y)` — orthogonalize x against y
- `sigmoid(x)` — sigmoid transform to (0,1)
- `tanh(x)` — tanh transform to (-1,1)

**Cross-Sectional:** compare across stocks same day
- `rank(x)` — rank (0->1) across universe
- `zscore(x)` — z-score cross-sectional
- `normalize(x)` — normalize to sum=1
- `scale(x)` — scale to leverage=1
- `winsorize(x, std)` — clip outliers
- `quantile(x, driver, n)` — divide into n groups

**Group Operators:** within-group calculations
- `group_neutralize(x, group)` — subtract group mean
- `group_rank(x, group)` — rank within group
- `group_zscore(x, group)` — z-score within group
- `group_vector_neut(x, driver, group)` — neutralize driver within group

Valid groups: `market`, `sector`, `industry`, `subindustry`

**Broken operators — DO NOT USE:**
`ts_min`, `ts_max`, `delay`, `stddev`, `correlation`, `delta`,
`ts_log_returns`. Use alternatives: `ts_arg_min/ts_arg_max`,
`ts_delay`, `ts_std_dev`, `ts_corr`, `ts_delta`,
`log(close / ts_delay(close, d))`.

### Step 3: Build Formula

**Basic template (1 line):**
```
rank( ts_<operation>( <data_field>, <lookback> ) )
```

**Advanced template (multi-line):**
```python
lookback = <N>;
signal   = <main_calculation>;
// add conditions or neutralization if needed
rank(signal)
```

**Examples:**
```python
# Version 1 (raw, 1 line):
-ts_delta(close, 5)

# Version 2 (normalized):
-rank(ts_delta(close, 5))

# Version 3 (multi-line + regime filter):
lookback = 5;
signal   = -rank(ts_delta(close, lookback) / (ts_std_dev(returns, 20) + 0.001));
when     = ts_rank(ts_std_dev(returns, 22), 252) > 0.5;
trade_when(when, signal, -1)
```

### Step 4: Choose Initial Settings

```
Universe:       TOP3000
Neutralization: Market
Decay:          0
Truncation:     0.05
Region:         USA
Delay:          1
```

### Step 5: Run Simulation & Evaluate

Check results then apply Workflow B or C.

---

## Common Data Fields

**Price & Volume:**
`open`, `high`, `low`, `close`, `volume`, `dvol` (close*volume),
`vwap`, `returns`, `adv5`, `adv20`

**Market & Size:**
`market_cap` (close*sharesout), `cap`, `sharesout`

**Fundamental (quarterly):**
`pb`, `pe`, `ps`, `pcf`, `debt_to_assets`, `roe`, `roa`,
`sales`, `ebitda`

**Short Selling:**
`short_ratio`, `short_interest`

**Always use `ts_backfill()` with fundamental fields.**
Safe example: `rank(ts_backfill(pe))`

---

## Core Quantitative Concepts (From Knowledge Base)

### Beta & CAPM
Beta measures systematic risk: Cov(Ri, Rm) / Var(Rm).
CAPM: Expected Return = Rf + Beta * (Rm - Rf).
In alpha: neutralize market beta via Market neutralization or
`vector_neut(signal, rank(returns))`.

### Sharpe Ratio
Sharpe = (Portfolio Return - Rf) / StdDev(Portfolio).
Sharpe >= 1.25 is target for submission.
Sharpe 1.0-1.25 is borderline — needs settings optimization.
Sharpe < 1.0 needs formula improvement NOT settings.

### Correlation & Covariance
- Correlation measures linear relationship strength (-1 to +1)
- Use `ts_corr(x, y, d)` to capture co-movement
- Alpha #13 from 101 Formulaic Alphas: `-rank(ts_covariance(rank(close), rank(volume), 5))`
- Use `group_neutralize` to remove sector/industry correlation bias

### Mean Reversion vs Momentum
- Mean Reversion: price reverts to mean (negative autocorrelation)
- Momentum: trend continues (positive autocorrelation)
- Key insight: alpha needs to pick ONE direction — don't mix both
- Short-term (1-5d) favors mean reversion
- Medium-term (10-60d) favors momentum

### Value at Risk (VaR)
Maximum expected loss at given confidence level.
95% VaR = -1.645 * sigma (if normal).
Track max drawdown — should be < 20%.

### Market Microstructure
- Bid-Ask spread, order book dynamics, market impact
- Important for turnover management
- High turnover > 70% means signal is noise-dominated

### Stationarity & Time Series
- Stationary series: mean and variance constant over time
- Price is non-stationary, returns are stationary
- Always use returns or normalized price in formulas

---

## Technical Indicators Reference (Built-in)

### RSI (Relative Strength Index)
RSI = 100 - 100 / (1 + RS), RS = Avg Gain / Avg Loss.
Overbought > 70, Oversold < 30.
Formula: `rank(-rsi(close, 14))` for mean reversion.

### MACD
MACD = EMA(12) - EMA(26), Signal = EMA(MACD, 9).
Crossovers signal trend changes.
Formula: `rank(ts_macd(close, 12, 26, 9))`.

### Bollinger Bands
Middle = SMA(20), Upper = +2sigma, Lower = -2sigma.
Price touching lower band + mean reversion = buy.
Formula: `rank((close - ts_mean(close, 20)) / ts_std_dev(close, 20))`.

### ATR (Average True Range)
True Range = max(H-L, H-prevC, prevC-L).
ATR measures volatility — use for position sizing.
Formula: `rank(ts_atr(high, low, close, 14))`.

### OBV (On-Balance Volume)
OBV = cumulative volume, +/- based on close direction.
Divergence between OBV and price signals reversal.
Formula: `rank(ts_obv(close, volume, 20))`.

### Volume-Weighted Average Price (VWAP)
VWAP = sum(price*volume) / sum(volume).
Price above VWAP = bullish, below = bearish.
Formula: `rank(vwap - close)` (proven Sharpe ~1.6).

### Stochastic Oscillator
%K = (close - lowest low) / (highest high - lowest low) * 100.
Overbought > 80, Oversold < 20.
Formula: `rank(ts_stoch(close, high, low, 14))`.

---

## Quantitative Methods Reference (Built-in)

### Pairs Trading
Trade a long-short pair of cointegrated stocks.
Requires: cointegration test + Z-score entry/exit.
Related: `Cointegration.md`, `Statistical_Arbitrage.md`.

### Machine Learning in Finance
- Linear regression for factor construction
- Decision trees for regime classification
- PCA for dimensionality reduction of alpha factors
- Key: avoid overfitting (use 70/20/10 splits)

### Risk Parity
Allocate risk equally, not capital.
Higher volatility assets get lower allocation.
Use in multi-alpha portfolio construction.

---

## Workflow B — Optimize Existing Alpha

**Entry condition:** Sharpe >= 1.0. If < 1.0, see Workflow C.

### Fitness Formula

```
Fitness = Sharpe * sqrt(|Returns| / max(Turnover, 0.125))
```

**Submission target:** Fitness >= 1.0, Sharpe >= 1.25, Turnover 10%-70%

### Optimization Table

| Problem | Cause | Solution |
|---|---|---|
| Turnover > 70% | Signal changes too fast | Increase Decay to 3-10 |
| Low Fitness despite good Sharpe | Turnover too low (<12.5%) | Decrease Decay to 0-2 |
| Sharpe < 1.0 | Weak signal | Change Neutralization -> Subindustry |
| Low Returns | Universe too small | TOP500 -> TOP1000/TOP3000 |
| Drawdown > 20% | Concentrated positions | Decrease Truncation to 0.03 |

### Recommended Optimization Grid

```
1. TOP3000 + Market    + Decay 0  + Truncation 0.05  <- try first
2. TOP3000 + Market    + Decay 3  + Truncation 0.05
3. TOP3000 + Subind.   + Decay 0  + Truncation 0.05
4. TOP1000 + Subind.   + Decay 10 + Truncation 0.10
5. TOP500  + Subind.   + Decay 0  + Truncation 0.10  <- highest Sharpe
```

### Universe Guide

| Universe | Stocks | When |
|---|---|---|
| TOP200 | 200 | VWAP, intraday, blue-chip signals |
| TOP500 | 500 | Strong signals, Subindustry neutral |
| TOP1000 | 1000 | Most common, most valid alphas |
| TOP3000 | 3000 | More small caps, higher returns |

Start with TOP3000, then try TOP1000.

### Neutralization Guide

| Type | When |
|---|---|
| None | Already clean alpha, volume-based |
| Market | Price-volume, mean reversion (default) |
| Sector | Avoid sector bets |
| Industry | Cross-industry alpha |
| Subindustry | Highest Sharpe, use with TOP500 |

Key insight: Price-volume alpha -> use Market, NOT Subindustry.
Subindustry reduces Sharpe but increases Fitness for fundamental.

### Decay Guide

| Decay | Typical Turnover | When |
|---|---|---|
| 0 | 30%-70% | Clear signal, low noise |
| 3 | 15%-40% | Slightly high turnover |
| 5 | 10%-25% | Best balance for most |
| 10 | 5%-15% | Slow signal, fundamental alpha |
| 20+ | < 5% | Rare, Fitness usually low |

If Turnover > 50%, try Decay=5. If > 70%, try Decay=10.

### Truncation Guide

| Truncation | Meaning | When |
|---|---|---|
| 0.01 (1%) | Very diversified | Large universe |
| 0.05 (5%) | Balanced (default) | Most alphas |
| 0.10 (10%) | Fewer stocks | TOP500/TOP1000 |
| 0.20 (20%) | Concentrated | TOP200, very strong signal |

---

## Workflow C — Diagnose & Fix Errors

### Formula Error vs Settings Issue

```
Sharpe < 0        -> Reverse direction: flip sign
0 < Sharpe < 0.5  -> Severe: signal nearly random
                    -> Change theme completely
0.5 <= Sharpe < 1 -> Moderate: fix formula first, tune later
Sharpe >= 1       -> No formula fix needed, go to Workflow B
```

### NaN / No Results

Most common causes:
1. **Division by zero:** add epsilon `+ 0.001`
2. **Log of negative/zero:** `log(volume + 1)` or `pasteurize(log(volume))`
3. **StdDev = 0:** add epsilon `+ 0.001`
4. **Fundamental fields NaN:** use `ts_backfill()`
5. **Constant series in ts_corr:** ensure both inputs have variance

Debug: `pasteurize(your_formula)` — if still error, test parts separately.

### Look-Ahead Bias (CRITICAL)

Symptom: Sharpe > 4.0 (abnormally high).
Cause: Using future data to predict future.
Fix: ALWAYS use Delay=1 in settings. Never use `ts_delay(x, 0)`.

### Overfitting

Symptom: High overall Sharpe but bad recent years.
Check: year-by-year performance.
Test robustness:
- Change lookback +/- 2 days
- Change universe
- Change neutralization

### Signal Too Weak (Sharpe 0.3-0.8)

Try in this order:
```
1. Flip sign (Sharpe 0.4 -> could become 1.2)
2. Change data field (close -> vwap -> returns)
3. Change lookback: 5 -> 10 -> 20
4. Wrap in rank() if not already
5. Change operator: ts_delta -> ts_mean -> ts_std_dev
6. If still < 0.8 after 5 steps -> abandon, try new theme
```

### Abnormally High Turnover

Turnover > 100%:
```python
# WRONG — flips direction daily
sign(ts_delta(close, 1))

# FIX — add smoothing
ts_decay_linear(sign(ts_delta(close, 1)), 10)
sign(ts_delta(close, 10))
```

Turnover < 2%: Decrease Decay to 0, or combine with price signal.

### Common Operator Mistakes

| User writes | Problem | Correct |
|---|---|---|
| `rank(close, 20)` | rank() has no lookback | `ts_rank(close, 20)` |
| `corr(x, y, 10)` | Doesn't exist | `ts_corr(x, y, 10)` |
| `std(returns, 20)` | Doesn't exist | `ts_std_dev(returns, 20)` |
| `log_return(close, 1)` | Doesn't exist | `log(close / ts_delay(close, 1))` |
| `ts_rank(x)` | Missing lookback | `ts_rank(x, 20)` |
| `group_neutralize(x)` | Missing group | `group_neutralize(x, sector)` |
| `rank(x) * rank(y)` | Scale mismatch | `rank(rank(x) * rank(y))` |

### Classification Quick Guide

```
Negative Sharpe?
  -> Flip entire formula sign

All NaN?
  -> Check division by zero, log of negative

Fitness < 0.5, Turnover > 50%?
  -> Wrap: ts_decay_linear(formula, 5)

Fitness < 0.5, Turnover < 10%?
  -> Set Decay=0, change Neutralization

Sharpe > 1.5 but rejected "too similar"?
  -> Change lookback +/- 2 days
  -> Change 1 data field

Syntax error?
  -> Check parentheses matching
  -> Check operator names (see operators reference)
```

---

## Advanced Syntax

### Multi-line Variables

```python
// Each statement ends with ;
// Last line has NO semicolon — that's the return value
lookback = 20;
vol      = ts_std_dev(returns, 20);
signal   = -ts_delta(close, lookback) / (vol + 0.001);
rank(signal)       // <-- no semicolon, this is the output
```

### Regime Filter Pattern (Proven)

```python
// Proven alpha (Sharpe 1.94, top 1.3% IQC)
lookback = 10;
mr   = -rank((close - ts_delay(close, 2)) / ts_delay(close, 2) / (ts_std_dev(returns, 20) + 0.001));
when = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;
b    = trade_when(when, mr, -1);
group_vector_neut(b, ts_mean(returns, 120), subindustry)
```

### group_vector_neut

More powerful than group_neutralize:
- Removes correlation with a specific vector driver within groups
- Syntax: `group_vector_neut(x, driver, group)`

### Common Conditions for Regime Filter

| Regime | Condition |
|---|---|
| High volatility | `ts_rank(ts_std_dev(returns,22), 252) > 0.55` |
| Volume surge | `ts_rank(volume / adv20, 5) > 0.7` |
| Strong momentum | `ts_rank(abs(ts_delta(close,20)), 252) > 0.6` |
| Low volatility | `ts_rank(ts_std_dev(returns,22), 252) < 0.3` |

Use `-1` in trade_when to hold position (lower turnover),
`NaN` to exit completely.

---

## Theme Formulas Reference

### Mean Reversion
```python
# Basic: buy stocks that dropped most this week
-rank(ts_delta(close, 5))

# Smoothed: reduce turnover
rank(ts_decay_linear(-ts_delta(close, 5), 3))

# Using returns instead of price
-rank(ts_mean(returns, 5))

# Low volume filter (avoid momentum trap)
if_else(ts_rank(volume, 20) < 0.5, -rank(ts_delta(close, 5)), 0)
```
Settings: TOP3000, Market, Decay 0-3, Truncation 0.05
Best lookback: 5-20 days

### Momentum
```python
# Short-term (1-5d)
rank(ts_mean(returns, 5))

# Medium-term (1-3 months)
rank(ts_delta(close, 20))

# Momentum minus recent reversal
rank(ts_delta(ts_delay(close, 5), 15))

# Rank-based momentum
ts_mean(rank(returns), 10)
```
Settings: TOP1000-3000, Subindustry, Decay 3-5
Best lookback: 20-60 days

### Volume-Price
```python
# Proven alpha #13 from 101 Formulaic Alphas
-rank(ts_covariance(rank(close), rank(volume), 5))

# Volume surge + low price
rank(ts_rank(volume, 20)) * -rank(ts_delta(close, 5))

# Money flow (close > open = positive)
rank(ts_sum(sign(close - open) * volume, 10))

# Volume-weighted returns
rank(ts_mean(returns * volume, 5) / ts_mean(volume, 5))
```
Settings: TOP3000, Market, Decay 0

### VWAP Deviation
```python
# Basic: deviation from VWAP
rank(vwap - close)

# Normalized by volatility
rank((vwap - close) / ts_std_dev(close, 20))

# VWAP reversion with volume filter
rank((vwap - close) / close) * rank(ts_rank(volume, 20))

# Combined with peak timing (IQC top alpha)
(vwap - close) / close / (ts_decay_linear(rank(ts_arg_max(close, 30)), 1) + 0.15)
```
Settings: TOP200-500, Market, Decay 0, Truncation 0.01

### Volatility
```python
# Short volatility (low vol stocks outperform)
-rank(ts_std_dev(returns, 20))

# Volatility reversal
-rank(ts_std_dev(returns, 5) / ts_std_dev(returns, 20))

# Spike detection
-rank(ts_std_dev(returns, 5) - ts_mean(ts_std_dev(returns, 5), 20))

# Range-based volatility
rank(-ts_mean((high - low) / close, 10))
```
Settings: TOP1000, Subindustry, Decay 5

### High-Low Midpoint
```python
# Basic
rank((high + low) / 2 - close)

# Multi-day
rank(ts_mean((high + low) / 2 - close, 5))

# Normalized by range
rank((close - low) / (high - low + 0.001))
```

### Fundamental Value
```python
# Value: low P/E = cheap = buy
rank(-ts_backfill(pe))

# Value: low P/B
rank(-ts_backfill(pb))

# Quality: high ROE
rank(ts_backfill(roe))

# Combined Value + Quality
rank(-ts_backfill(pe)) + rank(ts_backfill(roe))

# Earnings Yield
rank(1 / ts_backfill(pe))

# Sales growth momentum
rank(ts_delta(ts_backfill(sales), 252))
```
Settings: TOP500-1000, Subindustry, Decay 10-20, Truncation 0.10
Always use `ts_backfill()` with fundamental fields.

### Liquidity
```python
# Amihud Illiquidity
rank(ts_mean(abs(returns) / (close * volume + 1), 20))

# Volume abnormal vs average
rank(volume / adv20)

# Dollar volume abnormal
rank(dvol / ts_mean(dvol, 20))

# Volume turnover ratio
rank(volume / sharesout)

# Liquidity drop -> bearish
rank(-ts_delta(adv20, 5))

# Short ratio high -> squeeze risk
rank(-ts_backfill(short_ratio))
```
Settings: TOP3000, Market, Decay 3-5, Truncation 0.05

---

## Proven Alpha Templates

```python
# Mean Reversion (Sharpe ~1.4)
-rank(ts_delta(close, 5))

# Volume-Price (101 Formulaic Alphas #13)
-rank(ts_covariance(rank(close), rank(volume), 5))

# VWAP Reversion (Sharpe ~1.6)
rank(vwap - close)

# High-Low Midpoint
rank((high + low) / 2 - close)

# Momentum
rank(ts_mean(ts_delta(close, 1), 10))

# Value (low P/E)
rank(-ts_backfill(pe))

# Liquidity (Amihud)
rank(pasteurize(ts_mean(abs(returns) / (dvol + 1), 20)))

# Regime-filtered mean reversion (Sharpe 1.94)
lookback = 10;
mr   = -rank((close - ts_delay(close, 2)) / ts_delay(close, 2) / (ts_std_dev(returns, 20) + 0.001));
when = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;
b    = trade_when(when, mr, -1);
group_vector_neut(b, ts_mean(returns, 120), subindustry)
```

---

## IQC Competition Strategy

### Scoring System
- Bronze: > 1,000 pts (certificate)
- Silver: > 5,000 pts (special training)
- Gold: > 10,000 pts (eligible interview)

### Key Insight: IQC Rewards DIVERSITY
IQC scores baskets of alphas — uncorrelated alphas score higher.
Correlated alphas (even with high Sharpe) score lower.

### Strategy for 6-8 Submittable Alphas
```
- 2 price/volume alphas (short-term)
- 2 momentum/reversal (medium-term)
- 2 fundamental/sector
- 1-2 with special dataset (sentiment, news)
```

### Delay=0 Rule
Delay=0 IQC points are DIVIDED BY 3.
Only use if Fitness(D0) > 3 * Fitness(D1).

### Self-Correlation
Measured on PnL graph (2 years), NOT on formula/weights.
High correlation is OK if Sharpe improves >= 10%.
```
Example: old alpha Sharpe 1.40, new alpha corr 0.85, Sharpe 1.55
-> Sharpe improves 10.7% -> ALLOWED
```

### Fix Self-Correlation
1. Change lookback +/- 2-5 days
2. Change data field (close -> vwap)
3. Change operator (ts_delta -> ts_mean)
4. Add new dimension (volume)
5. Change universe
6. Change region

### Team Rules (2026)
- 1-4 members, all same university
- Register team: 17/3/2026 - 13/5/2026
- Divide themes: each person owns 2-3 different themes
- Avoid overlapping alphas in same team

### Submission Timeline
```
Days 1-7:     Test, find 2-3 formulas with Sharpe >= 1.25
Days 8-14:    Tune settings, submit 2 best alphas
Days 15-30:   Expand to new themes (Fundamental, Liquidity)
Month 2+:     Clone good alphas to other regions (CHN, EUR)
Daily:        Submit <= 1 new alpha (informal rate limit)
```

---

## Pre-Submit Checklist

### Required
- [ ] Sharpe >= 1.25
- [ ] Fitness >= 1.0
- [ ] Turnover 10%-70%
- [ ] No broken operators
- [ ] Drawdown < 25%
- [ ] Returns > 0%

### Stability Check (MOST IMPORTANT)
- [ ] No 2 consecutive years with negative Sharpe
- [ ] Positive Sharpe in at least 3/4 of years
- [ ] Worst year Sharpe >= -0.5
- [ ] Year-by-year PnL is consistently positive

### Robustness
- [ ] Test on >= 2 universes -> results consistent
- [ ] Test on >= 2 neutralizations -> results consistent
- [ ] Changing lookback +/- 2 doesn't crash Sharpe

### IQC Extra
- [ ] Different theme from last submitted alpha?
- [ ] High correlation? -> Sharpe improves >= 10%?
- [ ] Tried at least 2 regions? (USA + CHN/EUR)

---

## Stock Alpha Pipeline

Stock Alpha Pipeline là công cụ chạy Python compute factor thực tế & chọn cổ phiếu WQ Brain style.

### Chạy pipeline

```bash
# Default: S&P 500, TOP1000 universe
python run_pipeline.py

# Custom universe & top picks
python run_pipeline.py --universe TOP500 --top-n 20

# Custom date range & tickers
python run_pipeline.py --start 2024-01-01 --end 2025-12-31 --tickers AAPL MSFT GOOGL

# Bỏ cache (force re-download)
python run_pipeline.py --no-cache
```

### Pipeline output

| File | Nội dung |
|---|---|
| `pipeline_output/pipeline_results.json` | Daily top picks, factor stats, config |
| `pipeline_output/top_stocks_daily.csv` | CSV rank từng ngày: ticker, rank, score, signal |

### Alpha mặc định — Vol-Weighted Return Mean Reversion (proven)

Công thức gốc (WQ Brain):
```
lookback = 5;
raw_ret  = ts_sum(returns * volume, lookback) / (ts_sum(volume, lookback) + 1);
vol_std  = ts_std_dev(returns, 20);
vol_signal = -rank(raw_ret / (vol_std + 0.001));
```

| Bước | Giải thích |
|---|---|
| `ts_sum(returns * volume, 5)` | Dollar-weighted return 5 ngày (volume càng cao càng quan trọng) |
| `/ (ts_sum(volume, 5) + 1)` | Chuẩn hóa về VWAP-like return, +1 tránh division by zero |
| `/ (vol_std + 0.001)` | Divide by volatility — normalize risk |
| `-rank(...)` | Mean reversion: short khi vol-weighted return cao (đã pump), long khi thấp (đã dump) |

Pipeline mặc định dùng **chỉ 1 factor này** để screening.

### Factors đầy đủ (18 factors)

| Factor | WQ Brain Equivalent | Ý nghĩa |
|---|---|---|
| `vol_weighted_mr` **(default)** | `-rank(ts_sum(ret*vol,5) / (ts_sum(vol,5)+1) / (ts_std_dev(returns,20)+0.001))` | Vol-weighted return mean reversion |
| `mean_reversion_5` | `-rank(ts_delta(close, 5))` | Mean reversion ngắn hạn |
| `mean_reversion_10` | `-rank(ts_mean(returns, 10))` | Return reversal 2 tuần |
| `momentum_5/10/20` | `rank(ts_mean(returns, d))` | Momentum các khung |
| `volume_price_5` | `-rank(ts_covariance(rank(close), rank(volume), 5))` | Alpha #13 proven |
| `vwap_deviation` | `rank(vwap - close)` | VWAP reversion |
| `vwap_deviation_normalized` | `rank((vwap-close)/close/volatility)` | VWAP chuẩn hóa vol |
| `volatility_20` | `-rank(ts_std_dev(returns, 20))` | Low vol factor |
| `volatility_reversal` | `-rank(ts_std_dev(returns,5) / ts_std_dev(returns,20))` | Vol spike reversal |
| `high_low_midpoint` | `rank((high+low)/2 - close)` | Close position bias |
| `high_low_position` | `rank((close-low)/(high-low))` | Intraday strength |
| `liquidity_volume_ratio` | `rank(volume/adv20)` | Volume bất thường |
| `amihud_illiquidity` | `rank(ts_mean(abs(returns)/(dvol+1), 20))` | Illiquidity premium |
| `volume_surge` | `rank(ts_rank(volume, 20))` | Volume surge detection |
| `money_flow` | `rank(ts_sum(sign(close-open)*volume, 10))` | Money flow |
| `combined_mr_momentum` | `0.5*mr + 0.5*momentum` | Multi-factor combo |

### Dùng pipeline để tạo alpha

1. Chạy pipeline → xem ticker nào rank cao nhất
2. Phân tích factor nào đóng góp nhiều nhất cho ticker đó
3. Tạo WQ Brain formula từ factor tương ứng
4. Test simulation với settings phù hợp

### Ví dụ: Tạo alpha từ pipeline results

```
Pipeline output hôm nay: GS rank #1 với score cao nhất

→ Phân tích: GS có momentum mạnh + VWAP deviation dương
→ Tạo formula: rank(ts_mean(returns, 10)) + rank(vwap - close)
→ Settings: TOP500 | Subindustry | Decay 3 | Truncation 0.10
```

### Lưu ý khi dùng

- Pipeline dùng Python, KHÔNG phải WQ Brain simulation
- Dùng để screening ý tưởng, không thay thế backtest trên Brain
- Factor weights configurable trong `stock_pipeline/config.py`
- Universe: TOP200=200, TOP500=500, TOP1000=1000, TOP3000=3000 stocks top liquidity

---

## WQB Automation — Tự động submit alpha & đọc log

Script `wqb_automation.py` dùng Playwright để tự động login WQB, submit alpha, chờ simulation, đọc kết quả.

### Cài đặt

```bash
pip install playwright
python -m playwright install chromium
```

Tạo file `wqb_config.json` (đã có trong .gitignore):

```json
{
    "email": "namnguyen230304@gmail.com",
    "password": "pax230304",
    "headless": false,
    "timeout_ms": 300000
}
```

Hoặc dùng biến môi trường: `WQB_EMAIL`, `WQB_PASSWORD`, `WQB_HEADLESS=true`

### Cách dùng

```bash
# Formula đơn
python wqb_automation.py --formula "rank(ts_delta(close,5))"

# Formula + settings
python wqb_automation.py --formula "rank(ts_delta(close,5))" --settings "TOP500|Subindustry|3|0.10"

# Đọc từ file (nhiều formula, cách nhau blank line)
python wqb_automation.py --file alpha_list.txt

# Nhập tay
python wqb_automation.py --interactive

# Chạy ẩn (không mở browser)
python wqb_automation.py --formula "..." --headless
```

### Output

| File | Nội dung |
|---|---|
| `wqb_logs/alpha_<timestamp>.json` | Kết quả từng alpha (Sharpe, Fitness, Turnover, yearly) |
| `wqb_logs/*.png` | Screenshot debug từng bước |
| Console | Bảng comparison giữa các alpha |

### Login Flow (Đã verify thành công)

```
1. Navigate /sign-in
2. Fill email + password (CSS selectors: input[name="email"], input[name="password"])
3. Wait 2000ms cho ALTCHA auto-verify (altcha-widget shadow DOM, tự động verify)
4. Submit form: form.requestSubmit()   ← Đây là cách DUY NHẤT hoạt động
5. Chờ redirect (poll 20s, mỗi 1s kiểm tra URL)
6. Nếu redirect sang /simulate/tutorial hoặc /simulate/learn/courses:
   - Dismiss intro.js overlay (click skip button hoặc JS remove)
   - Force navigate về /simulate
```

**Critical**: `form.requestSubmit()` là cách duy nhất để submit login thành công. `button.click()` KHÔNG hoạt động vì React kiểm soát disabled state của nút.

### Simulate Flow (Đã test, đang debug lỗi)

```
1. Đảm bảo ở trang /simulate (nếu đang ở /learn/ thì force navigate)
2. Dismiss intro.js overlay (5 attempts)
3. Chờ Monaco editor render (poll 20s × 1s)
4. Set formula text: nativeInputValueSetter + dispatch input event
5. Dismiss cookie banner (cky-btn-accept)
6. Click Simulate button:
   - Try 1: Playwright click(force=True) trên button.editor-simulate-button-text
   - Try 2: JS dispatchEvent MouseEvent('click')
   - Try 3: Focus textarea + Ctrl+Enter
7. Click Results checkbox
8. Wait results (120 attempts × 5s = 10 phút)
9. Parse metrics từ HTML
```

### Known Bug — Simulate Error

Sau khi click Simulate, server trả về:
```
"WorldQuant BRAIN is experiencing some difficulties. Please contact support if this problem persists."
```

Đã thử:
- Playwright force click ✓
- JS dispatchEvent click ✓
- Ctrl+Enter keyboard shortcut ✓
- Re-trigger simulate mỗi 5 attempts ✓
- Tất cả đều ra cùng error

**Root cause chưa xác định**: có thể do:
1. Formula syntax không hợp lệ mặc dù editor không báo lỗi
2. Server-side rate limiting trên account
3. Cần refresh ALTCHA token trước mỗi simulation
4. Page state không đúng (đang ở /simulate nhưng React state là learn sub-page)

### Monaco Editor Interaction

WQB Monaco Editor không thể type bằng Playwright fill() thông thường.
Phải dùng JS để bypass React synthetic events:

```javascript
const textarea = document.querySelector('textarea[aria-roledescription="editor"]');
const setter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, 'value'
).set;
setter.call(textarea, formula);
textarea.dispatchEvent(new Event('input', { bubbles: true }));
```

### ALTCHA Anti-Bot

- Custom element: `altcha-widget` (shadow DOM)
- Auto-verify sau khi fill credentials
- Không cần tương tác thủ công
- `data-state="verified"` là verified
- Token có TTL — có thể cần refresh cho mỗi simulation

### Intro.js Overlay

Sau login, WQB có thể hiện tutorial overlay (intro.js).
Xử lý:
1. Click `.introjs-skipbutton` nếu visible
2. Nếu không, JS remove: `document.querySelector(".introjs-overlay")?.remove()`

### CookieYes Banner

Banner cookie (cky-consent-container) overlay lên các button.
Luôn dismiss trước khi click bất kỳ button nào: click `.cky-btn-accept`.

### Lưu ý

- Cần có kết nối internet ổn định
- Nếu WQB thay đổi giao diện, selectors trong script cần cập nhật
- Chạy **không headless** lần đầu để xem browser làm gì
- Nếu login fail, xem `wqb_logs/login_failed.png` và `after_login.png`
- Xem `AGENTS_README.md` cho reference chi tiết về variables, flow, known issues

---

## Alpha Agent — Autonomous Research Loop

Agent tự động: research docs → hypothesis → viết alpha → submit WQB → đọc log → phân tích → cải thiện → loop.

### Chạy

```bash
# Dry-run (kiểm tra logic, không chạm WQB)
python alpha_agent.py --quick

# Live (tự động login WQB, submit, loop)
python alpha_agent.py --headless    # ẩn browser
python alpha_agent.py               # có browser
python alpha_agent.py --max-cycles 10
```

### Agent workflow

```
  ┌─────────────────────────────────────┐
  │  RESEARCH Knowledge Base            │
  │  - 8 themes, operators, settings   │
  └──────────┬──────────────────────────┘
             ↓
  ┌─────────────────────────────────────┐
  │  HYPOTHESIS Generator               │
  │  - Pick untested theme              │
  │  - Economic rationale               │
  │  - Generate formula variants        │
  └──────────┬──────────────────────────┘
             ↓
  ┌─────────────────────────────────────┐
  │  WRITE Alpha Formula (WQ syntax)    │
  └──────────┬──────────────────────────┘
             ↓
  ┌─────────────────────────────────────┐
  │  SUBMIT to WQB via Playwright       │
  │  - Login via form.requestSubmit()   │
  │  - Set formula in Monaco editor     │
  │  - Click Simulate (Playwright force)│
  │  - Wait simulation (tối đa 10 phút)│
  └──────────┬──────────────────────────┘
             ↓
  ┌─────────────────────────────────────┐
  │  ANALYZE Results                    │
  │  - Parse Sharpe, Fitness, Turnover  │
  │  - Diagnose failures                │
  │  - Compare yearly stability         │
  └──────────┬──────────────────────────┘
             ↓
     ┌─── PASS? ───┐
     │             │
    YES            NO
     │             │
     ▼             ▼
  Optimize     Diagnose & fix
  settings      │
  grid          ├─ Wrong sign → flip
                ├─ Weak signal → change field/lookback
                ├─ High TO → add decay
                ├─ Unstable → add regime filter
                ├─ Server error → retry later / different formula
                └─ All failed → new theme
                     │
                     ▼
               Loop back to RESEARCH
```

### Diagnosis Rules (embedded in agent)

| Symptom | Sharpe | Fix |
|---|---|---|
| Wrong sign | < -0.5 | Flip `-` sign |
| Weak signal | 0 ~ 0.5 | Change field, lookback, add rank() |
| Moderate | 0.5 ~ 1.0 | Add vol normalization, regime filter |
| High turnover | > 70% | ts_decay_linear(sig, 5) |
| Unstable | negative years | trade_when + group_vector_neut |
| Low fitness | < 1.0 | Run settings grid (5 rounds) |
| Server error | N/A | "experiencing difficulties" — retry different formula, refresh session |

### Current Status — Known Blockers

- **Login**: ✅ Hoạt động ổn định với `form.requestSubmit()`
- **Formula entry**: ✅ Hoạt động với Monaco editor JS API
- **Simulate click**: ✅ Click được (Playwright force + JS dispatch + Ctrl+Enter)
- **Simulation result**: ❌ Server trả về error "experiencing difficulties" — chưa rõ nguyên nhân
- **Gold alphas saved**: 0 (chưa có simulation nào pass)

### Output

| File | Nội dung |
|---|---|
| `wqb_logs/gold_alphas.json` | Alpha đã pass (Sharpe ≥ 1.25 + Fitness ≥ 1.0) |
| `wqb_logs/alpha_<ts>.json` | Log từng lần submit |
| Console | Bảng comparison, diagnosis, suggestions |

## Knowledge Base Overview

### Dataset Statistics
- Total documents: 214
- Categories: 6
- Version: 2.0 (deduplicated, properly categorized)

### Category Breakdown

| Category | Files | Description |
|---|---|---|
| core_concepts | 66 | Beta, CAPM, Sharpe, VaR, Correlation, etc. |
| research_insights | 52 | Alpha research tips, community strategies, Brain tricks |
| technical_indicators | 37 | RSI, MACD, Bollinger, VWAP, ATR, OBV, etc. |
| platform_guides | 22 | WorldQuant Brain docs, data explorer, submission guide |
| academic_papers | 19 | Classic papers (Fama, Markowitz, Kahneman, etc.) |
| quantitative_methods | 18 | Pairs trading, risk parity, ML in finance, etc. |

### Improvements in v2.0
1. Removed 153 duplicate files
2. Fixed miscategorization (Investopedia -> correct categories)
3. Added quantitative_methods category
4. Properly separated academic papers from community content
5. No cross-category duplicates

### Source References

| File | Content |
|---|---|
| `references/operators.md` | All operators, data fields, broken operators |
| `references/themes.md` | 10 themes with formulas: Mean Rev, Momentum, Volume, VWAP, Volatility, High-Low, Sector, Fundamental, Liquidity, Regime-Based |
| `references/advanced-syntax.md` | Multi-line expression, variables, trade_when, group_vector_neut |
| `references/settings-grid.md` | Universe, Neutralization, Decay, Truncation, Multi-Region optimization |
| `references/iqc-strategy.md` | IQC scoring, Delay=0 penalty, self-correlation, team rules, submission timeline |
| `references/checklist.md` | Pre-submit checklist, stability check, robustness tests |
| `references/common-mistakes.md` | NaN debug, look-ahead bias, overfitting, operator errors |
