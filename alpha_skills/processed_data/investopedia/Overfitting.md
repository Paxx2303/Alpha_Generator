# Overfitting

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A modeling error that occurs when a function is too closely fit to a limited set of historical data points, causing out-of-sample failure.

---

## 🔢 Mathematical Formula

$$\text{Error}_{in} \approx 0 \text{ but } \text{Error}_{out} \gg 0$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Ultimate alpha killer. WQ Brain implements Out-of-Sample (OS) testing to detect and reject overfitted alphas.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*