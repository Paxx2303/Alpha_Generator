# Standard Deviation

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A statistical measure of market volatility, showing how much prices deviate from their average.

---

## 🔢 Mathematical Formula

$$\sigma = \sqrt{\frac{\sum (X_i - \bar{X})^2}{n}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Total volatility. In WQ Brain: `ts_std_dev(close, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*