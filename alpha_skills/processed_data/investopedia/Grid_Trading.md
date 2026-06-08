# Grid Trading

**Category:** Trading Strategies & Concepts 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A technique where buy and sell orders are placed at regular intervals above and below a predefined base price.

---

## 🔢 Mathematical Formula

$$\text{Grid Intervals} = P_{base} \pm i \times \Delta P$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Exploits range-bound volatility. Extremely common in currency markets.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*