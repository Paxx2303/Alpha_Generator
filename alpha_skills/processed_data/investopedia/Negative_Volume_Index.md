# Negative Volume Index

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A cumulative indicator that identifies smart money flow on days when trading volume decreases from the previous day.

---

## 🔢 Mathematical Formula

$$\text{NVI}_t = \text{NVI}_{t-1} + \text{returns}_t \text{ (if } V_t 70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*