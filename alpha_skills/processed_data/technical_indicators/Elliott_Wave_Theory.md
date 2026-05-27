# Elliott Wave Theory

**Category:** Classic Trading Theories  
**Source:** Investopedia / Technical Analysis Reference

---

## 📝 Definition

**Elliott Wave Theory** is a form of technical analysis that describes price movements in financial markets as repeating cycles called "waves". Developed by Ralph Nelson Elliott in the 1930s, the theory posits that market cycles result from investor psychology and herd behavior, which manifests in predictable patterns of impulse waves (trending) and corrective waves (counter-trending).

### Wave Structures
The basic Elliott Wave pattern consists of a **5-wave impulse sequence** followed by a **3-wave corrective sequence** (referred to as a 5-3 wave pattern):
1. **Impulse Waves (1, 2, 3, 4, 5):** 
   - **Wave 1:** Initial price move.
   - **Wave 2:** Correction of Wave 1 (never retraces more than 100% of Wave 1).
   - **Wave 3:** Usually the longest and most powerful wave (never the shortest of the three impulse waves).
   - **Wave 4:** Correction of Wave 3 (never enters the price territory of Wave 1).
   - **Wave 5:** Final push, often displaying high volume and speculation.
2. **Corrective Waves (A, B, C):**
   - **Wave A:** Initial downward correction.
   - **Wave B:** Bear market rally, retracing part of Wave A.
   - **Wave C:** Deep downward wave, usually breaking past the bottom of Wave A.

### Three Rules of Elliott Wave Impulse Waves
- **Rule 1:** Wave 2 cannot retrace more than 100% of Wave 1.
- **Rule 2:** Wave 3 is typically the longest of the three impulse waves and can never be the shortest.
- **Rule 3:** Wave 4 cannot overlap with the territory of Wave 1 (the peak of Wave 1).

---

## 🔢 Fibonacci Ratios in Elliott Wave

Elliott Waves are closely linked to Fibonacci ratios:
- Wave 2 retracement is typically $50\%$ to $61.8\%$ of Wave 1.
- Wave 3 is often $1.618 \times$ the length of Wave 1.
- Wave 4 correction is typically $38.2\%$ of Wave 3.

---

## 💡 Application in Alpha Design (WorldQuant Brain)

While exact wave counting is complex for simple formulas, we can capture the core wave psychology (Wave 3 acceleration and Wave 5 exhaustion):

1. **Wave 3 Momentum Acceleration (Buying the Strongest Wave):**
   Identify stocks that have cleared a consolidation range, showing high volume and accelerating price momentum:
   ```python
   momentum_1 = ts_delta(close, 5);
   momentum_2 = ts_delta(close, 20);
   volume_ratio = volume / ts_mean(volume, 20);
   // Wave 3 represents dual-scale accelerating momentum confirmed by volume
   wave_3_signal = momentum_1 * momentum_2 * volume_ratio;
   rank(wave_3_signal)
   ```

2. **Wave 5 Exhaustion / Divergence (Selling the Exhaustion):**
   Identify stocks making a new high, but with decreasing momentum and volume (typical Wave 5 characteristics):
   ```python
   is_new_high = close > ts_delay(ts_max(high, 20), 1);
   momentum_drop = ts_delta(close, 5) < ts_delay(ts_delta(close, 5), 5);
   volume_drop = volume < ts_mean(volume, 20);
   exhaustion = is_new_high && momentum_drop && volume_drop;
   // Mean reversion: short exhaustion peaks
   signal = if_else(exhaustion, -1.0, 0.0);
   rank(signal)
   ```

---

*Prepared as part of the Alpha Creator Skill raw data package.*
