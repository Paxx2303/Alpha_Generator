# Trend Following

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A strategy that attempts to capture gains through the analysis of an asset's momentum in a particular direction.

---

## 🔢 Mathematical Formula

$$\text{Signal} = \text{sign}(P_t - \text{Moving Average}_t)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Longer-term momentum. WQ Brain: `sign(close - ts_mean(close, 50))`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
