# Stationary Process

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A stochastic process whose unconditional joint probability distribution does not change when shifted in time.

---

## 🔢 Mathematical Formula

$$E(X_t) = \mu, \quad \text{Var}(X_t) = \sigma^2, \quad \text{Cov}(X_t, X_{t-k}) = \gamma_k$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Required for regression models. Raw stock prices are non-stationary; stock *returns* are stationary.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*