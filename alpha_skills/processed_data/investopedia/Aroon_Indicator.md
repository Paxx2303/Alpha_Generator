# Aroon Indicator

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A technical indicator used to identify trend changes and strength by measuring the time between highs and lows.

---

## 🔢 Mathematical Formula

$$\text{Aroon Up} = \frac{n - \text{Days Since } n\text{-day High}}{n} \times 100$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures timing of recent peaks. In WQ Brain: `ts_arg_max(high, n)` and `ts_arg_min(low, n)` which return days since max/min.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*