# R Squared

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A statistical measure representing the proportion of variance for a dependent variable that's explained by an independent variable.

---

## 🔢 Mathematical Formula

$$R^2 = 1 - \frac{\text{SS}_{res}}{\text{SS}_{tot}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures benchmark fit. High R-Squared (e.g. >90%) indicates the portfolio returns mimic the benchmark.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*