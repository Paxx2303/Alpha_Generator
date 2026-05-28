# Jensen Alpha

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Measures the excess return of a portfolio above its expected return calculated using CAPM.

---

## 🔢 Mathematical Formula

$$\alpha = R_p - [R_f + \beta_p(R_m - R_f)]$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Represents the manager's value-add or 'pure skill'. Ultimate goal of WQ Brain alphas is pure alpha.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
