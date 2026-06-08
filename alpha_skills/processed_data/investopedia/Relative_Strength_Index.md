# Relative Strength Index

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A momentum oscillator that measures the speed and change of price movements, fluctuating between 0 and 100.

---

## 🔢 Mathematical Formula

$$\text{RSI} = 100 - \frac{100}{1 + \text{RS}}, \quad \text{RS} = \frac{\text{Average Gain}}{\text{Average Loss}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Identifies overbought (>70) and oversold (70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*