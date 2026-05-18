# Fitness Optimization Playbook - 2026-05-18

Purpose:
- Help Hermes and DeerFlow optimize for WorldQuant fitness, not only Sharpe.
- Convert data and settings research into concrete generation rules.

## Fitness Objective

- WorldQuant-style fitness is commonly expressed as:
  `Fitness = Sharpe * sqrt(abs(Returns) / max(Turnover, 0.125))`
- Practical implication:
  once turnover is already below `0.125`, pushing turnover even lower usually helps less than improving Sharpe or Returns.
- Practical implication:
  if turnover is above `0.125`, reducing turnover can improve fitness materially.

## Data-Driven Levers

### 1. Slower data often helps fitness

- Slower-moving datasets such as fundamentals, analyst revisions, and some news aggregates often produce lower turnover than short-horizon price-only signals.
- If the signal is built from rapidly changing price or volume, fitness often suffers unless the horizon is stretched or the trading is filtered.

Agent rule:
- Prefer slower horizons for price-volume motifs unless there is evidence that short-horizon trading is still efficient.

### 2. Match neutralization to the data category

- Community WorldQuant notes suggest that the right neutralization depends on the data source:
  fundamentals and earnings usually benefit from industry-style neutralization, while broad price-volume ideas can work with coarser neutralization.
- For some simple price-reversion alphas, moving from subindustry neutralization to market neutralization can lower Sharpe but improve fitness.

Agent rule:
- If Sharpe is acceptable but fitness is weak, test alternative neutralization before discarding the idea.

### 3. Turnover control matters most above the 0.125 floor

- Higher decay reduces turnover.
- Event-based trading such as `trade_when(event, alpha, -1)` can reduce unnecessary rebalancing.
- Longer lookbacks often reduce daily signal churn.

Agent rule:
- If turnover is above `0.125`, first try higher decay, longer lookback, or event filtering.
- If turnover is already near or below `0.125`, focus more on improving signal quality and returns.

### 4. Liquidity-aware ideas can improve efficiency

- Volume or liquidity should not only be a direct signal; they can be used as gating or weighting information to avoid noisy trades.
- Price-volume interaction can help returns, but raw short-horizon volume ratios can become crowded.

Agent rule:
- Use volume as confirmation or conditioning information, not only as a standalone rank.

### 5. Universe choice affects fitness

- Smaller and more liquid universes can help returns and execution quality, but can also change neutralization behavior and concentration.
- For broad TOP3000 universes, many ideas need stronger smoothing or data normalization to avoid high-turnover noise.

Agent rule:
- When the same idea has poor fitness in a broad universe, test whether it needs stronger smoothing assumptions.

## Safe Rules For Current System

Because the current validator and generators are intentionally conservative, apply these rules first:

1. Prefer `N=20` or `N=60` when the goal is fitness-first generation.
2. Use `N=5` or `N=10` only when the formula is clearly a short-horizon continuation or reversal idea.
3. Favor `close / ts_mean(close, N) - 1` and `ts_delta(close, N) / ts_std_dev(close, N)` over raw return averages when short windows produce weak fitness.
4. Favor `ts_corr(volume, returns, N)` over plain `volume / ts_mean(volume, N)` when volume-only formulas appear too noisy.
5. If a formula already has low turnover but poor fitness, work on Sharpe and Returns rather than reducing turnover further.

## Generation Hints For Hermes And DeerFlow

- Ask for “fitness-first” alphas, not “high Sharpe only.”
- Ask whether the formula is likely above or below the turnover floor.
- Ask what data category is driving the edge:
  price trend, price-vs-mean, volatility-normalized move, or volume confirmation.
- Ask which setting change is most likely to improve fitness:
  lookback, decay, neutralization, or truncation.

## Sources

- WorldQuant Learn2Quant:
  https://www.worldquant.com/learn2quant/
- WorldQuant alpha trading community notes:
  https://github.com/alexisdpc/WorldQuant-alpha-trading
- Community notes on metrics and neutralization:
  https://github.com/jglazar/notes/blob/main/quant_interview/submitted_alphas.md
- Community notes on alpha ideas and fitness behavior:
  https://github.com/jglazar/notes/blob/main/quant_interview/alpha_ideas.md
- Improvement strategies summary:
  https://deepwiki.com/xiegengcai/world-quant-brain/4.2-improvement-strategies
