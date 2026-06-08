# Ease of Movement

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An oscillator that analyzes the relationship between price change and volume to gauge the ease of price rises or falls.

---

## 🔢 Mathematical Formula

$$\text{EMV} = \frac{\text{Midpoint Move}}{\text{Box Ratio}}, \quad \text{Box Ratio} = \frac{\text{Volume} / 1M}{\text{High} - \text{Low}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures price ease. In WQ Brain: `ts_mean(((high + low)/2 - (ts_delay(high,1) + ts_delay(low,1))/2) / (volume / (high - low + 0.001)), n)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*