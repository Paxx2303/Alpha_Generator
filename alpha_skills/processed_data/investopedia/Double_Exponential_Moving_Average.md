# Double Exponential Moving Average

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A fast moving average that reduces lag by subtracting a double-smoothed EMA from a single-smoothed EMA.

---

## 🔢 Mathematical Formula

$$\text{DEMA} = (2 \times \text{EMA}) - \text{EMA}(\text{EMA})$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Ultra-low lag trend tracking. In WQ Brain: can be constructed by nesting EMA approximations.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*