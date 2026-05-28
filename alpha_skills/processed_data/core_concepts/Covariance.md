# Covariance

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A measure of the directional relationship between the returns on two risky assets.

---

## 🔢 Mathematical Formula

$$\text{Cov}(X, Y) = \frac{\sum(X_i - \bar{X})(Y_i - \bar{Y})}{n}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

WQ Brain operator: `ts_covariance(x, y, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
