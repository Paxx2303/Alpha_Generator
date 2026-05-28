# Mean Reversion

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A financial theory suggesting that asset prices and historical returns eventually return to their long-term average.

---

## 🔢 Mathematical Formula

$$\Delta P_t = -\lambda (P_{t-1} - \mu) + \epsilon_t$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Very common theme. WQ Brain template: `-(close - ts_mean(close, 5))` or `rank(vwap - close)`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
