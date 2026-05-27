# Keltner Channels

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

Volatility-based envelopes set above and below an exponential moving average, using Average True Range (ATR).

---

## 🔢 Mathematical Formula

$$\text{Upper} = \text{EMA} + (2 \times \text{ATR}), \quad \text{Lower} = \text{EMA} - (2 \times \text{ATR})$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Identifies breakouts and price channels. In WQ Brain: similar to Bollinger Bands, using typical price and ATR proxies.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
