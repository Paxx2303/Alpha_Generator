# Tail Risk

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The risk that an investment will perform more than three standard deviations from its mean, indicating extreme event risk.

---

## 🔢 Mathematical Formula

$$P(X < \mu - 3\sigma) > \text{Normal Probability}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Avoided by diversifying signals and using robust scaling operators like `winsorize`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
