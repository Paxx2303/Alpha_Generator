# Hull Moving Average

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An extremely fast and smooth moving average that almost eliminates lag while maintaining smoothing.

---

## 🔢 Mathematical Formula

$$\text{HMA} = \text{WMA}\left(2 \times \text{WMA}(P, \frac{n}{2}) - \text{WMA}(P, n), \sqrt{n}\right)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Fast trend tracking. In WQ Brain: can be approximated using multiple nested `ts_decay_linear` operators.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
