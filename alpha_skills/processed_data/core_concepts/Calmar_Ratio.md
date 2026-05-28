# Calmar Ratio

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A performance metric that compares annualized rate of return to maximum drawdown.

---

## 🔢 Mathematical Formula

$$\text{Calmar} = \frac{\text{Annualized Return}}{\text{Maximum Drawdown}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

High Calmar indicates high returns with very low drawdowns. Target Calmar > 2.0 is excellent.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
