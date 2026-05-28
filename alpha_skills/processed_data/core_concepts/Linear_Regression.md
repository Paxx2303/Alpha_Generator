# Linear Regression

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A statistical method used to model the linear relationship between a dependent variable and one or more independent variables.

---

## 🔢 Mathematical Formula

$$Y = \beta_0 + \beta_1 X + \epsilon$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Used to project future prices or check beta. In WQ Brain: `ts_regression(close, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
