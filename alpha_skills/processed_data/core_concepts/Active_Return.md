# Active Return

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The excess return of a portfolio relative to its benchmark.

---

## 🔢 Mathematical Formula

$$\text{Active Return} = R_p - R_b$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Represents raw outperformance before risk adjustment.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
