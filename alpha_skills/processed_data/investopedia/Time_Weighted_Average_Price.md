# Time Weighted Average Price

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A trading benchmark representing the average price of a security over a specified time, dividing the day into equal slices.

---

## 🔢 Mathematical Formula

$$\text{TWAP} = \frac{\sum_{i=1}^N P_i}{N}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Execution benchmark. In WQ Brain: can be represented as `ts_mean(close, n)` for equal-interval slices.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*