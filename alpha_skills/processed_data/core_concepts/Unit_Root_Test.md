# Unit Root Test

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A statistical test to determine whether a time series variable is non-stationary and has a unit root.

---

## 🔢 Mathematical Formula

$$\Delta Y_t = \gamma Y_{t-1} + \epsilon_t \text{ (ADF Test)}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Used to verify stationarity of spreads in mean reversion strategies.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
