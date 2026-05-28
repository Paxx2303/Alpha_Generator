# Average Directional Index

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An indicator used to quantify trend strength, regardless of trend direction, moving between 0 and 100.

---

## 🔢 Mathematical Formula

$$\text{ADX} = 100 \times \text{EMA}\left(\frac{|+\text{DI} - -\text{DI}|}{+\text{DI} + -\text{DI}}\right)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Filters out range-bound markets. In WQ Brain: can be used as a regime filter: `trade_when(adx > 25, trend_signal, reversion_signal)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
