# Regime-Aware Alpha Generation

## Core Principle
Different market regimes favor different alpha families:

| Regime | Best Alpha Types | Avoid |
|--------|------------------|-------|
| **Bull / Low Vol** | Momentum, Trend-following | Aggressive mean-reversion |
| **Bear / High Vol** | Mean-reversion, Volatility-normalized | Pure price momentum |
| **Choppy / Sideways** | Volume-price correlation, Liquidity provision | High-turnover signals |
| **Earnings Season** | Fundamental + price dislocation | Pure technical |

## Practical Implementation for Hermes/DeerFlow

### Daily Research Injection
Every generation cycle should receive a short regime summary from `daily_researcher`:

```
REGIME SUMMARY:
- Volatility: High (VIX > 25)
- Liquidity: Normal
- Recent factor performance: Value and Low-Vol outperforming
→ Prefer: Volatility-normalized + mean-reversion signals
```

### Prompt Template Addition
```
CURRENT MARKET REGIME:
{regime_summary}

GENERATION GUIDANCE:
- In high-vol regimes: emphasize volatility normalization and volume confirmation
- In low-vol regimes: momentum and trend signals perform better
- Always include at least one volume component unless explicitly pure momentum
```

## Evaluation Check
In post-simulation review, ask:
> "Is this alpha likely to survive the current volatility and liquidity regime?"

**Last Updated:** 2026-05-19
