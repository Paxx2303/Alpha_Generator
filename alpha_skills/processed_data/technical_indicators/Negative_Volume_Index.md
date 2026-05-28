# Negative Volume Index

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A cumulative indicator that identifies smart money flow on days when trading volume decreases from the previous day.

---

## 🔢 Mathematical Formula

$$\text{NVI}_t = \text{NVI}_{t-1} + \text{returns}_t \text{ (if } V_t < V_{t-1}\text{)}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Tracks institutional buying. In WQ Brain: `ts_sum(if_else(volume < ts_delay(volume, 1), returns, 0), n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
