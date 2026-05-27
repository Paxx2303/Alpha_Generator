# On Balance Volume

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A momentum indicator that uses volume flow to predict changes in stock price, accumulating volume on up days and subtracting on down days.

---

## 🔢 Mathematical Formula

$$\text{OBV}_t = \text{OBV}_{t-1} + \text{sign}(\text{Close}_t - \text{Close}_{t-1}) \times \text{Volume}_t$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures volume pressure. In WQ Brain: `ts_sum(sign(ts_delta(close, 1)) * volume, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
