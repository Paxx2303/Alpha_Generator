# Statistical Arbitrage

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A class of quantitatively driven trading strategies that exploit pricing inefficiencies between related financial assets.

---

## 🔢 Mathematical Formula

$$\text{Spread} = Y - \beta X, \quad \text{Trade if } \text{Z-Score}(\text{Spread}) > k$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Pairs trading and cross-sectional mean reversion. WQ Brain enforces this by neutralizing sector biases.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
