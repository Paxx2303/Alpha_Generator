# Dollar Cost Averaging

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An investment strategy where an investor divides the total amount to be invested into periodic purchases of a target asset.

---

## 🔢 Mathematical Formula

$$\text{Investment}_t = \text{Constant}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Reduces market timing risk and dampens short-term volatility effects.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
