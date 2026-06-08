# Triple Exponential Moving Average

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An even faster moving average that reduces lag further by using triple-smoothed EMAs.

---

## 🔢 Mathematical Formula

$$\text{TEMA} = (3 \times \text{EMA}) - (3 \times \text{EMA}(\text{EMA})) + \text{EMA}(\text{EMA}(\text{EMA}))$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Zero-lag trend filtering. In WQ Brain: nested recursive logic.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*