# Volume Weighted Average Price

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A technical analysis indicator showing the average price a security has traded at, weighted by volume.

---

## 🔢 Mathematical Formula

$$\text{VWAP} = \frac{\sum (\text{Price} \times \text{Volume})}{\sum \text{Volume}}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Identifies fair value. In WQ Brain: `vwap` data field. Deviation: `(vwap - close) / close` is an excellent mean reversion signal.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*