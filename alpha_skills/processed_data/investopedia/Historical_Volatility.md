# Historical Volatility

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The realized volatility of a security's price over a specified past timeframe.

---

## 🔢 Mathematical Formula

$$\text{HV} = \text{StdDev}(\ln(P_t/P_{t-1})) \times \sqrt{252}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Measures actual past price dispersion. Used in volatility breakout and reversion alphas.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*