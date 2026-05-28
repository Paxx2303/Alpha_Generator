# P Value

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The probability of obtaining test results at least as extreme as the results actually observed, assuming the null hypothesis is true.

---

## 🔢 Mathematical Formula

$$p = P(\text{Test Statistic} \ge \text{Observed Value} \mid H_0)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Checks model validity. A p-value < 0.05 indicates statistical significance.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
