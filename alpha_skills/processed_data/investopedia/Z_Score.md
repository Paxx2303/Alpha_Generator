# Z Score

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A numerical measurement that describes a value's relationship to the mean of a group of values, measured in standard deviations.

---

## 🔢 Mathematical Formula

$$Z = \frac{X - \mu}{\sigma}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

WQ Brain operators: `zscore(x)` (cross-sectional) and `ts_zscore(x, n)` (time-series). Prevents scale bias.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*