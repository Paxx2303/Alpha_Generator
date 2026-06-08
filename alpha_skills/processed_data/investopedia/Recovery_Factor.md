# Recovery Factor

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Measures how quickly and effectively a portfolio recovers from its maximum drawdown.

---

## 🔢 Mathematical Formula

$$\text{Recovery Factor} = \frac{\text{Total Profit}}{\text{Maximum Drawdown}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

A high recovery factor (>3.0) shows a robust, self-correcting alpha strategy.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*