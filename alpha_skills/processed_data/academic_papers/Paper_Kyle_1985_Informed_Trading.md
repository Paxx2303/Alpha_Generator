# Continuous Auctions and Informed Traders (Kyle, 1985)

**Authors:** Albert S. Kyle  
**Year:** 1985  
**Journal:** Econometrica  
**Topic:** Market Microstructure / Adverse Selection  

---

## 📝 Core Summary

This seminal paper in **Market Microstructure** models a financial market with three types of participants: a single informed trader, noise traders (liquidity traders who trade randomly), and market makers. Kyle established a model of price formation where informed traders strategically hide their trades among noise traders.

Key concepts introduced:
- **Kyle's Lambda (Liquidity Measure):** A measure of market depth and illiquidity, representing the price impact of order flow.
- **Informed Order Flow:** Order flow carries information. Market makers adjust prices upward when they see buy order imbalances, fearing they are trading with an informed buyer (adverse selection).

---

## 🔢 Kyle's Lambda Formula

The pricing rule of the market maker is linear:
$$P_t = P_0 + \lambda (y_t)$$

Where:
- $y_t = x_t + u_t$ is the total order flow (informed order flow $x_t$ plus noise order flow $u_t$).
- $\lambda$ (Kyle's Lambda) represents the price impact of a unit of order flow:
  $$\lambda = \frac{\text{Cov}(v, y)}{\text{Var}(y)}$$
  ($v$ is the true value of the asset).

---

## 💡 Application in WorldQuant Brain

Kyle's Lambda highlights the relationship between order imbalances and subsequent price moves:

1. **Volume and Price Move Interaction (OFI Proxy):**
   Alphas can predict short-term price moves by measuring volume imbalances:
   ```python
   // Buy stocks experiencing upward order flow pressure (price increase on high volume)
   price_change = ts_delta(close, 1);
   imbalance = price_change * volume;
   // Smooth to create short-term predictive signal
   signal = ts_mean(imbalance, 5);
   rank(signal)
   ```
2. **Liquidity Provision (Mean Reversion on High Illiquidity):**
   Stocks with high illiquidity (large Kyle's Lambda) experience large price impacts from noise trading. These price impacts represent temporary deviations and tend to revert:
   ```python
   // Amihud Illiquidity proxy: absolute return divided by dollar volume
   illiquidity = ts_mean(abs(returns) / (volume * close + 1), 20);
   // Revert prices that had large moves on high illiquidity
   signal = -rank(returns) * illiquidity;
   rank(signal)
   ```

---

*Prepared as part of the Alpha Creator Skill research paper raw data package.*
