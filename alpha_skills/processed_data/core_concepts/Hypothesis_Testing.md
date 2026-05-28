# Hypothesis Testing

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An act in statistics whereby an analyst tests an assumption regarding a population parameter.

---

## 🔢 Mathematical Formula

$$H_0 \text{ vs } H_a$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Used to validate if an alpha formula actually generates outperformance (excess return > 0).

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
