# Money Flow Index

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A technical oscillator that uses both price and volume to identify overbought or oversold signals in an asset.

---

## 🔢 Mathematical Formula

$$\text{MFI} = 100 - \frac{100}{1 + \text{Money Ratio}}, \quad \text{Money Ratio} = \frac{\text{Positive Money Flow}}{\text{Negative Money Flow}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Volume-weighted version of RSI. In WQ Brain: calculating volume-weighted price changes over a lookback window.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*