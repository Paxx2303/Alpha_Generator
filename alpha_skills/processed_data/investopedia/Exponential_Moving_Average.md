# Exponential Moving Average

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A type of moving average that places a greater weight and significance on the most recent data points.

---

## 🔢 Mathematical Formula

$$\text{EMA}_t = [V_t \times (\frac{2}{1+n})] + \text{EMA}_{t-1} \times [1 - (\frac{2}{1+n})]$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Responds faster to price changes than SMA. In WQ Brain: can be approximated using `ts_decay_linear` or custom recursive expressions.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*