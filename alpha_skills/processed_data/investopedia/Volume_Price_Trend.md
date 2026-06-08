# Volume Price Trend

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An indicator that combines price percentage change and volume to confirm trend strength and detect divergence.

---

## 🔢 Mathematical Formula

$$\text{VPT}_t = \text{VPT}_{t-1} + \left(\frac{\text{Close}_t - \text{Close}_{t-1}}{\text{Close}_{t-1}}\right) \times \text{Volume}_t$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Volume-weighted momentum. In WQ Brain: `ts_sum(ts_delta(close, 1) / ts_delay(close, 1) * volume, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*