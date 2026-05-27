# Breakout Trading

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A strategy where a trader enters a position when an asset's price breaks above a resistance level or below support.

---

## 🔢 Mathematical Formula

$$\text{Buy if } P_t > \max(P_{t-1}...P_{t-n})$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Momentum strategy. In WQ Brain: `close > ts_max(high, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
