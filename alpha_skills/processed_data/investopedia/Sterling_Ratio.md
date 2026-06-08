# Sterling Ratio

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A risk-adjusted return ratio that compares return to average maximum drawdown.

---

## 🔢 Mathematical Formula

$$\text{Sterling} = \frac{\text{Return}}{\text{Average Max Drawdown} - 10\%}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Alternative risk metric focusing on drawdown consistency.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*