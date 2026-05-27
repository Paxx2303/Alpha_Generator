# Value at Risk

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A statistic that quantifies the maximum potential loss of a portfolio over a specific timeframe at a given confidence level.

---

## 🔢 Mathematical Formula

$$\text{VaR}_{\alpha} = \inf \{ L \mid P(Loss > L) \le 1 - \alpha \}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Key institutional risk measure. Guides truncation and leverage limits.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
