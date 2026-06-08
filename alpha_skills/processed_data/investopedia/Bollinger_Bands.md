# Bollinger Bands

**Category:** Technical Indicators 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A technical analysis tool defined by a set of trendlines plotted two standard deviations away from a simple moving average.

---

## 🔢 Mathematical Formula

$$\text{Upper Band} = \text{SMA} + (k \times \sigma), \quad \text{Lower Band} = \text{SMA} - (k \times \sigma)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures volatility and identifies price extremes. In WQ Brain: `(close - ts_mean(close, n)) / ts_std_dev(close, n)` (Z-Score deviation).

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*