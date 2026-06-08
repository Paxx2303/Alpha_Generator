# Bootstrap Resampling

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A statistical method that uses random sampling with replacement to estimate the distribution of a statistic.

---

## 🔢 Mathematical Formula

$$X^* = \text{Sample with replacement from } X$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Used to estimate Sharpe ratio confidence intervals and test robustness.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*