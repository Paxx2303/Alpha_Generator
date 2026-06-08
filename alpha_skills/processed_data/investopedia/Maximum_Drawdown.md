# Maximum Drawdown

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The maximum observed loss from a peak to a trough of a portfolio, before a new peak is attained.

---

## 🔢 Mathematical Formula

$$\text{MDD} = \frac{\text{Peak Value} - \text{Trough Value}}{\text{Peak Value}} \times 100$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

WQ Brain constraint: Drawdown must be low (70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*