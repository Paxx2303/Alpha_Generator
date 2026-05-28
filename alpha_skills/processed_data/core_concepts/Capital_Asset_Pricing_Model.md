# Capital Asset Pricing Model

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A model describing the relationship between systematic risk and expected return for assets.

---

## 🔢 Mathematical Formula

$$E(R_i) = R_f + \beta_i (E(R_m) - R_f)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Forms the theoretical baseline for risk-adjusted performance and beta calculations.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
