# Sharpe Ratio

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Measures the risk-adjusted return of an investment portfolio compared to a risk-free rate.

---

## 🔢 Mathematical Formula

$$\text{Sharpe} = \frac{R_p - R_f}{\sigma_p}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Core WQ Brain simulation metric. Must be >1.25 for submission. Increased by raising returns or lowering volatility.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*