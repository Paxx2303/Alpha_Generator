# Parabolic SAR

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A technical indicator used to determine the price direction of an asset and draw attention to when the direction is changing.

---

## 🔢 Mathematical Formula

$$\text{SAR}_{t+1} = \text{SAR}_t + \text{AF} \times (\text{EP} - \text{SAR}_t)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Trailing stop and trend indicator. In WQ Brain: typically used as a regime indicator to filter trend signals.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
