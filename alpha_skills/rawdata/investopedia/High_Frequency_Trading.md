# High Frequency Trading

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A method of trading that uses powerful computers to transact a large number of orders in fractions of a second.

---

## 🔢 Mathematical Formula

$$\text{Latency} < 1 \text{ millisecond}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Relies on tick data and order book depth. WQ Brain operates on daily/intraday delay, not HFT.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
