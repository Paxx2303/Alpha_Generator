# Implied Volatility

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A metric reflecting the market's expectation of future volatility, derived from option prices.

---

## 🔢 Mathematical Formula

$$\text{Option Price} = f(\text{Asset Price}, \text{Strike}, T, R_f, \text{IV})$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Forward-looking volatility. In WQ Brain: options data fields (like option implied volatility skew) are very predictive.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*