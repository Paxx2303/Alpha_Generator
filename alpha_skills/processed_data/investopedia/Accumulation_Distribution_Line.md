# Accumulation Distribution Line

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A volume-based indicator that measures the cumulative flow of money into and out of a security.

---

## 🔢 Mathematical Formula

$$\text{ADL}_t = \text{ADL}_{t-1} + \left(\frac{(\text{Close} - \text{Low}) - (\text{High} - \text{Close})}{\text{High} - \text{Low}}\right) \times \text{Volume}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures buying power. In WQ Brain: `ts_sum(((close - low) - (high - close)) / (high - low + 0.001) * volume, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*