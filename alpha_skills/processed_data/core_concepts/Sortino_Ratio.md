# Sortino Ratio

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A variation of the Sharpe ratio that only penalizes negative excess returns (downside deviation).

---

## 🔢 Mathematical Formula

$$\text{Sortino} = \frac{R_p - R_f}{\sigma_d}, \quad \sigma_d = \text{Standard Deviation of Negative Returns}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Evaluates downside-adjusted returns. High Sortino indicates positive skewness in returns.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
