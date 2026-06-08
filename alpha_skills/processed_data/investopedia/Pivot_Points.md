# Pivot Points

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An intraday technical indicator used to identify support, resistance, and the overall market trend.

---

## 🔢 Mathematical Formula

$$\text{PP} = \frac{H + L + C}{3}, \quad R_1 = (2 \times \text{PP}) - L, \quad S_1 = (2 \times \text{PP}) - H$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Intraday support/resistance. In WQ Brain: using daily `high`, `low`, and `close` to project next day bounds.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*