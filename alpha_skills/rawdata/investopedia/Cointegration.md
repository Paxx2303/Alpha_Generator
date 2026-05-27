# Cointegration

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A statistical property of time series variables where a linear combination of non-stationary series is stationary.

---

## 🔢 Mathematical Formula

$$Y_t - \beta X_t = u_t \text{ (where } u_t \text{ is stationary)}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

The mathematical foundation of Pairs Trading. Confirms stable long-term spreads.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
