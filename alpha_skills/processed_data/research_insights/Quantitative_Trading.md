# Quantitative Trading

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Trading strategies based on quantitative analysis, which rely on mathematical computations and number crunching.

---

## 🔢 Mathematical Formula

$$\text{Action} = f(\text{Data Inputs}, \Theta)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

The core discipline of WorldQuant. Every WQ Brain formula represents a quantitative trading model.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
