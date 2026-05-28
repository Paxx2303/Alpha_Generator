# Underfitting

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Occurs when a model is too simple to capture the underlying structure of the data, resulting in poor in-sample and out-of-sample performance.

---

## 🔢 Mathematical Formula

$$\text{Error}_{in} \gg 0 \text{ and } \text{Error}_{out} \gg 0$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Resolved by incorporating more predictive features and adjusting lookback windows.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
