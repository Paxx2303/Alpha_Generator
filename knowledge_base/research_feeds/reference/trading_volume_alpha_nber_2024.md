# Trading Volume Alpha (NBER Working Paper 33037, 2024)

## Core Finding
Volume contains predictive information **beyond price**. High-volume return premium (HVRP) is stronger when combined with negative contemporaneous correlation between return and volume changes (CCRV).

## Recommended Expression Patterns for Hermes/DeerFlow

### High-Impact Patterns
1. Volume-confirmed reversal:
   ```
   rank(-ts_delta(close, N)) * rank(ts_delta(volume, N))
   ```

2. Volume-return correlation:
   ```
   rank(ts_corr(volume, returns, N))
   ```

3. Volume vs mean with price dislocation:
   ```
   rank(volume / ts_mean(volume, N) - ts_delta(close, M) / ts_std_dev(close, M))
   ```

### Regime Notes
- Volume alpha performs best in **high liquidity regimes**
- Weaker on low-volume days or during earnings season
- Combine with volatility normalization for robustness

## Implementation Tip
Always include at least one volume component unless the strategy is explicitly pure price momentum.

**Source:** Goyenko, Kelly, Moskowitz, Su, Zhang — NBER 2024
