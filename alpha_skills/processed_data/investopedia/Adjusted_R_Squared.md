# Adjusted R Squared

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A modified version of R-squared that has been adjusted for the number of predictors in the model, penalizing unnecessary variables.

---

## 🔢 Mathematical Formula

$$\text{Adj } R^2 = 1 - \left[\frac{(1 - R^2)(n - 1)}{n - k - 1}\right]$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Protects against variable-inflation bias in multi-factor alpha models.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*