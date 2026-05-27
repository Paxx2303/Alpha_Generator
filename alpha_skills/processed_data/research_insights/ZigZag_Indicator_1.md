# ZigZag Indicator

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A technical tool that filters out noise by plotting points only when price moves by a percentage greater than a threshold.

---

## 🔢 Mathematical Formula

$$\text{Points} = P_t \text{ if } |P_t - P_{last}| / P_{last} \ge \text{Threshold}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Filters price noise. In WQ Brain: used to identify historical swing highs and lows.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
