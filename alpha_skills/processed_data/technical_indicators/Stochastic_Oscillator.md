# Stochastic Oscillator

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A momentum indicator comparing a closing price of a security to its price range over a certain period of time.

---

## 🔢 Mathematical Formula

$$\%\text{K} = \frac{\text{Current Close} - \text{Lowest Low}}{\text{Highest High} - \text{Lowest Low}} \times 100$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures location of close relative to lookback range. In WQ Brain: `ts_scale(close, n)` (which scales the value between 0 and 1).

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
