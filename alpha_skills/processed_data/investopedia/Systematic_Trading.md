# Systematic Trading

**Category:** Trading Strategies & Concepts 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A method of trading where all decisions are made based on a set of rules defined by models, eliminating human bias.

---

## 🔢 Mathematical Formula

$$\text{Rules} = \text{Fixed } \Rightarrow \text{Trades} = \text{Deterministic}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Allows unbiased backtesting and historical validation. WQ Brain is 100% systematic.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*