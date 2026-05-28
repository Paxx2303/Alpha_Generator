# Risk Reward Ratio

**Category:** Risk & Performance Metrics  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Measures the prospective reward an investor can earn for every dollar risked on a trade.

---

## 🔢 Mathematical Formula

$$\text{RRR} = \frac{\text{Target Profit}}{\text{Stop Loss Value}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Crucial for positive mathematical expectation. High RRR allows low Win Rate strategies to be highly profitable.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
