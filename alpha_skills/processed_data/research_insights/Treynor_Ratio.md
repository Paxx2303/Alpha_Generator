# Treynor Ratio

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Measures the risk-adjusted return of a portfolio based on systematic risk (Beta) rather than total risk.

---

## 🔢 Mathematical Formula

$$\text{Treynor} = \frac{R_p - R_f}{\beta_p}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Useful for diversified portfolios. High Treynor indicates strong performance per unit of market risk.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
