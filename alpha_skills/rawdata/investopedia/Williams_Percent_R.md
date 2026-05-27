# Williams Percent R

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A momentum indicator that reflects the level of the close relative to the highest high for the lookback period.

---

## 🔢 Mathematical Formula

$$\text{Williams } \%\text{R} = \frac{\text{Highest High} - \text{Close}}{\text{Highest High} - \text{Lowest Low}} \times -100$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Similar to Stochastic %K but inverted. In WQ Brain: `-ts_scale(close, n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
