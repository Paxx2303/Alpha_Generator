# Expected Shortfall

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Coherent risk metric representing the average loss in the worst-case scenario at a given confidence level.

---

## 🔢 Mathematical Formula

$$\text{ES} = \frac{1}{1-\alpha} \int_{\alpha}^1 \text{VaR}_u \, du$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Used for tail-risk hedging and margin calculations in systematic trading.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*