# WorldQuant Metric Playbook - 2026-05-17

This note summarizes how to interpret common WorldQuant-style simulation metrics and what changes usually move them.

## Core Metrics

- Sharpe: risk-adjusted return. Higher Sharpe usually means the signal is more consistent, not just more profitable.
- Fitness: combines Sharpe, returns, and turnover. A signal with decent Sharpe can still have weak Fitness if turnover is too high.
- Returns: annualized average gain or loss relative to book size.
- Turnover: daily trading activity. Higher turnover often means the signal is too reactive, more fragile, or more expensive to trade.
- Drawdown: largest peak-to-trough loss. High drawdown usually means the signal is exposed to regime shifts or crowded risk.
- Self-correlation: similarity versus existing alphas or PnL patterns. Lower is better for uniqueness and submission diversity.

## Practical Reading Guide

- High Sharpe + high Fitness + moderate turnover:
  usually a robust family worth expanding with nearby lookbacks and neutralization variants.
- High Sharpe + low Fitness:
  often means turnover is too high, so decay, event filters, or smoother operators may help.
- High returns + bad drawdown:
  often means the alpha is exploiting a narrow regime and needs better neutralization or less concentrated bets.
- Low self-correlation + acceptable Sharpe:
  often worth keeping because it adds diversity even if it is not the single top-return alpha.
- Repeatedly high turnover:
  check whether the expression is too short-horizon or whether `decay` is too low.

## Parameter Implications

- Decay:
  higher decay usually smooths signals and reduces turnover.
- Delay:
  delay 1 is typically easier to pass than delay 0, but may reduce raw responsiveness.
- Truncation:
  tighter truncation usually reduces single-name concentration and can improve drawdown stability.
- Neutralization:
  stronger neutralization can reduce hidden sector or industry bets and make performance more portable.
- Universe:
  more liquid universes are usually easier operationally, but sometimes lose niche signal strength.

## Agent Heuristics

- If Fitness is weak, first inspect turnover before changing the hypothesis.
- If Drawdown is the main problem, inspect concentration, neutralization, and regime sensitivity.
- If Self-correlation is high, preserve the economic idea but change the operator family, horizon, or conditioning event.
- If Sharpe is weak across a whole family, the hypothesis may be wrong for the current market regime.

## Sources

- WorldQuant BRAIN overview:
  https://www.worldquant.com/brain/
- Community notes with parameter and metric formulas:
  https://github.com/jglazar/notes/blob/main/quant_interview/submitted_alphas.md
- WorldQuant alpha trading notes with turnover and fitness guidance:
  https://github.com/alexisdpc/WorldQuant-alpha-trading
- Self-correlation system explanation:
  https://deepwiki.com/xiegengcai/world-quant-brain/4.1-self-correlation-analysis
- Finding Alphas book excerpt:
  https://notes.yeshiwei.com/_downloads/9a536da31207cc1942b82e5769782af6/WorldQuant_FindingAlphas.pdf
