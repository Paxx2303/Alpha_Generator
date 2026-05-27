# Force Index

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An indicator that uses price and volume to assess the power behind a price move and identify potential turning points.

---

## 🔢 Mathematical Formula

$$\text{FI} = (\text{Close}_t - \text{Close}_{t-1}) \times \text{Volume}_t$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Combines momentum and volume. In WQ Brain: `ts_delta(close, 1) * volume` smoothed with `ts_decay_linear`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
