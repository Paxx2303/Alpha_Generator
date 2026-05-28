# Relative Vigor Index

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An oscillator that measures trend strength by comparing a security's closing price to its price range while smoothing the result.

---

## 🔢 Mathematical Formula

$$\text{RVI} = \frac{\text{Close} - \text{Open}}{\text{High} - \text{Low}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures energy of the close. In WQ Brain: `ts_mean((close - open) / (high - low + 0.001), n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
