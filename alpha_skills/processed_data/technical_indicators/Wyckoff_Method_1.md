# Wyckoff Method

**Category:** Classic Trading Theories  
**Source:** Investopedia / Technical Analysis Reference

---

## 📝 Definition

The **Wyckoff Method** is a technical analysis approach to trading and investing developed by Richard Wyckoff in the early 20th century. It is based on studying supply and demand, price action, volume, and the phases of market cycles. Wyckoff proposed that big market players (the "Composite Man") accumulate or distribute shares before major trends begin.

### Three Laws of the Wyckoff Method
1. **The Law of Supply and Demand:** 
   - When demand is greater than supply, prices rise.
   - When supply is greater than demand, prices fall.
   - Volume represents the force behind demand and supply.
2. **The Law of Cause and Effect:**
   - The size of a price move (effect) is directly proportional to the amount of preparation or consolidation (cause) that preceded it.
   - Accumulation or distribution ranges represent the "cause" of subsequent markup or markdown trends.
3. **The Law of Effort vs. Result:**
   - Divergence between price action (result) and volume (effort) indicates a change in trend.
   - High volume (effort) without a significant price move (result) suggests that the dominant force is changing (e.g., buying effort met with massive distribution supply).

### Wyckoff Market Cycle
1. **Accumulation:** Composite Man buys shares quietly within a trading range. Characters include: Selling Climax (SC), Automatic Rally (AR), Secondary Test (ST), and Spring (shakeout below support).
2. **Markup (Bull Trend):** Price breaks out of the accumulation range and starts trending up.
3. **Distribution:** Composite Man sells shares to the late-coming public. Characters include: Buying Climax (BC), Automatic Reaction (AR), and Upthrust (UTAD - fake breakout above resistance).
4. **Markdown (Bear Trend):** Price breaks down and trends down.

---

## 🔢 Wyckoff Spread & Volume Analysis

Wyckoff relies on analyzing "spread" (High minus Low) and volume to identify institutional footprints:
- **High volume + wide spread + close near high:** Strong buying effort and results (Bullish).
- **High volume + narrow spread + close near middle/low:** Buying effort met with selling resistance (Bearish absorption).

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Wyckoff principles can be captured by checking volatility compression (cause) and volume-spread relationships (effort vs result):

1. **Effort vs Result Alpha (Volume-Spread Divergence):**
   Detect cases where price moves are small despite high volume (reversal setups):
   ```python
   spread = high - low;
   normalized_spread = spread / ts_mean(spread, 20);
   normalized_volume = volume / ts_mean(volume, 20);
   // High volume relative to spread suggests hidden resistance (distribution/accumulation)
   effort_vs_result = normalized_volume - normalized_spread;
   // Reversion signal: sell if price is at a local peak with high effort-vs-result
   signal = -rank(close) * effort_vs_result;
   rank(signal)
   ```

2. **Spring / Shakeout Detector:**
   Identify cases where price briefly breaks a multi-day low on high volume, then quickly recovers:
   ```python
   lookback = 20;
   local_min = ts_min(low, lookback);
   is_breakout = low < ts_delay(local_min, 1);
   is_recovery = close > ts_delay(local_min, 1);
   shakeout = is_breakout && is_recovery && (volume > ts_mean(volume, lookback));
   // Buy signal on confirmed shakeouts
   signal = if_else(shakeout, 1.0, 0.0);
   rank(signal)
   ```

---

*Prepared as part of the Alpha Creator Skill raw data package.*
