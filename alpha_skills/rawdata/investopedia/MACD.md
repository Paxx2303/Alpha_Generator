# MACD

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A trend-following momentum indicator that shows the relationship between two moving averages of a security’s price.

---

## 🔢 Mathematical Formula

$$\text{MACD} = \text{EMA}_{12} - \text{EMA}_{26}, \quad \text{Signal Line} = \text{EMA}_9(\text{MACD})$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Crossovers indicate momentum shifts. In WQ Brain: subtracting short-term averages from long-term averages: `ts_mean(close, 12) - ts_mean(close, 26)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
