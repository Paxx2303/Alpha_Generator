# Multicollinearity

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A phenomenon in which two or more predictor variables in a multiple regression model are highly correlated, skewing estimates.

---

## 🔢 Mathematical Formula

$$\text{Corr}(X_i, X_j) \approx 1$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Avoided in portfolios by ensuring alphas are uncorrelated with each other (low self-correlation).

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*