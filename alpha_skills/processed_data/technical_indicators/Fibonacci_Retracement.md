# Fibonacci Retracement

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A method of technical analysis for identifying support and resistance levels based on Fibonacci mathematical ratios.

---

## 🔢 Mathematical Formula

$$\text{Retracement Levels} = \text{Peak} - (\text{Peak} - \text{Trough}) \times \text{Ratio}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Identifies pullback targets. In WQ Brain: finding local peaks and troughs and calculating standard ratios (0.382, 0.618).

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
