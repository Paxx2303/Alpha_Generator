# Average True Range

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A volatility indicator that measures the average range of price movement, accounting for gaps and limit moves.

---

## 🔢 Mathematical Formula

$$\text{TR} = \max(\text{High}-\text{Low}, |\text{High}-\text{Close}_{prev}|, |\text{Low}-\text{Close}_{prev}|)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures absolute volatility. In WQ Brain: `ts_mean(high - low, n)` or using `ts_std_dev` of returns as a proxy.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
