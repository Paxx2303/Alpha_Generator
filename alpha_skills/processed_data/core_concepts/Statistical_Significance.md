# Statistical Significance

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A determination that a relationship between two or more variables is caused by something other than random chance.

---

## 🔢 Mathematical Formula

$$p < \alpha \text{ (typically } 0.05 \text{ or } 0.01\text{)}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Protects against overfitting and backtest mining (flukes).

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
