# Standard Error

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The standard deviation of the sampling distribution of a statistic, most commonly of the mean.

---

## 🔢 Mathematical Formula

$$\text{SE} = \frac{\sigma}{\sqrt{n}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures estimate precision. Guides confidence intervals for backtested returns.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*