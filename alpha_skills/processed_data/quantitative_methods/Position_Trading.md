# Position Trading

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A long-term trading strategy where a trader holds positions for weeks or months based on macroeconomic or fundamental trends.

---

## 🔢 Mathematical Formula

$$\text{Hold Period} > 30 \text{ days}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Relies on fundamental data. Tuned with high Decay parameters (e.g. Decay=10) to reduce turnover.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
