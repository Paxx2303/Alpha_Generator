# Modern Portfolio Theory

**Category:** Trading Strategies & Concepts 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A framework for assembling a portfolio of assets such that the expected return is maximized for a given level of risk.

---

## 🔢 Mathematical Formula

$$\sigma_p^2 = w^T \Sigma w, \quad R_p = w^T R$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Guides weight allocation in WQ Brain. Pasteurization and truncation limits prevent concentration risk.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*