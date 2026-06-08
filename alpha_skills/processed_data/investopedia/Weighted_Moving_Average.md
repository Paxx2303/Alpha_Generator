# Weighted Moving Average

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A moving average that assigns linearly decreasing weights to older data points.

---

## 🔢 Mathematical Formula

$$\text{WMA} = \frac{\sum_{i=1}^n i \times P_i}{\sum_{i=1}^n i}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Identical to linear decay. In WQ Brain: `ts_decay_linear(close, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*