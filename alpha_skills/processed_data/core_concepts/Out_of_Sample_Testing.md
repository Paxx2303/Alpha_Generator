# Out of Sample Testing

**Category:** Quantitative & Statistical Analysis  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The practice of testing a model's predictive power on a dataset that was not used during model training or parameter optimization.

---

## 🔢 Mathematical Formula

$$\text{Validation Set} \cap \text{Training Set} = \emptyset$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Mandatory in WQ Brain. Models must pass out-of-sample simulation test to be submitted.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
