# Rate of Change

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A pure momentum oscillator that measures the percentage change in price between the current price and a price n periods ago.

---

## 🔢 Mathematical Formula

$$\text{ROC} = \frac{\text{Close}_t - \text{Close}_{t-n}}{\text{Close}_{t-n}} \times 100$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures price momentum. In WQ Brain: `ts_delta(close, n) / ts_delay(close, n)` or simply `returns` for short windows.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
