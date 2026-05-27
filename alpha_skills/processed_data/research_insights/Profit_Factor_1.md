# Profit Factor

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The ratio of gross profits to gross losses over a specific trading period.

---

## 🔢 Mathematical Formula

$$\text{Profit Factor} = \frac{\sum \text{Profitable Trades}}{\sum \text{Losing Trades}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures strategy profitability. Excellent strategies have a profit factor > 1.5.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
