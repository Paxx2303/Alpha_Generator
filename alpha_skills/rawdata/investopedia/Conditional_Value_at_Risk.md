# Conditional Value at Risk

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A risk assessment metric that quantifies the average extreme losses in the tail of a distribution beyond the VaR threshold.

---

## 🔢 Mathematical Formula

$$\text{CVaR}_{\alpha} = E[Loss \mid Loss > \text{VaR}_{\alpha}]$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Also known as Expected Shortfall. Captures catastrophic tail risk better than VaR.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
