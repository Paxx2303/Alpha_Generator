# Beta

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Measures the sensitivity or systematic risk of a security or portfolio relative to the market.

---

## 🔢 Mathematical Formula

$$\beta = \frac{\text{Covariance}(R_p, R_m)}{\text{Variance}(R_m)}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Market exposure. WQ Brain enforces beta-neutrality through Market Neutralization, which sets portfolio beta to 0.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*