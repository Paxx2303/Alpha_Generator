# Ichimoku Cloud

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A collection of technical indicators that show support and resistance levels, as well as momentum and trend direction.

---

## 🔢 Mathematical Formula

$$\text{Tenkan-sen} = \frac{\max(H,9) + \min(L,9)}{2}, \quad \text{Kijun-sen} = \frac{\max(H,26) + \min(L,26)}{2}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Comprehensive support/resistance. In WQ Brain: formulas using `ts_arg_max` and `ts_arg_min` over 9, 26, and 52 days.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*