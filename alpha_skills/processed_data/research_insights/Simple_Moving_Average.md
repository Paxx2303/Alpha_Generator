# Simple Moving Average

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An arithmetic moving average calculated by adding recent prices and dividing by the number of time periods.

---

## 🔢 Mathematical Formula

$$\text{SMA} = \frac{\sum_{i=1}^n P_i}{n}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Used for trend smoothing and mean reversion. In WQ Brain: `ts_mean(close, n)`. Deviation from SMA: `close - ts_mean(close, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
