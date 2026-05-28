# Commodity Channel Index

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A momentum-based oscillator used to help determine when an investment vehicle is reaching overbought or oversold conditions.

---

## 🔢 Mathematical Formula

$$\text{CCI} = \frac{\text{Typical Price} - \text{SMA}(\text{Typical Price})}{0.015 \times \text{Mean Deviation}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures deviation from average typical price. In WQ Brain: using mean absolute deviation or `ts_std_dev` to normalize price deviation.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
