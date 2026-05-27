# Chaikin Money Flow

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An indicator that measures the volume-weighted average of accumulation and distribution over a specified period.

---

## 🔢 Mathematical Formula

$$\text{CMF} = \frac{\sum_{i=1}^n \text{Money Flow Multiplier}_i \times \text{Volume}_i}{\sum_{i=1}^n \text{Volume}_i}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Combines price range location and volume. In WQ Brain: `ts_mean(((close - low) - (high - close)) / (high - low + 0.001) * volume, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
