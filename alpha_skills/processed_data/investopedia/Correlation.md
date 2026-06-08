# Correlation

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Measures the degree to which two assets move in relation to each other.

---

## 🔢 Mathematical Formula

$$\rho = \frac{\text{Covariance}(X, Y)}{\sigma_X \sigma_Y}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

WQ Brain operator: `ts_corr(x, y, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*