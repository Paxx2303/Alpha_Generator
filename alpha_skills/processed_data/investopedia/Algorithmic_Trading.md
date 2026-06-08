# Algorithmic Trading

**Category:** Trading Strategies & Concepts 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The process of executing orders using automated pre-programmed trading instructions accounting for variables like time, price, and volume.

---

## 🔢 Mathematical Formula

$$\text{Order Execution} = g(\text{Market Conditions})$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Automates market making and arbitrage. Relies on TWAP/VWAP algorithms.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*