# Heteroskedasticity

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A condition in which the variance of the residual term in a regression model is not constant, violating OLS assumptions.

---

## 🔢 Mathematical Formula

$$\text{Var}(\epsilon_i) \ne \sigma^2 \text{ (varies with } i\text{)}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Very common in stock prices (volatility clustering). Resolved by GARCH models or z-score scaling.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
