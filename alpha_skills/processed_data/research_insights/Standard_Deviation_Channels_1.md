# Standard Deviation Channels

**Category:** Technical Indicators  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A technical analysis tool consisting of parallel lines plotted standard deviations away from a linear regression trendline.

---

## 🔢 Mathematical Formula

$$\text{Channel} = \text{Linear Regression Line} \pm (k \times \sigma)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Trend following and mean reversion. In WQ Brain: combining `ts_regression` and `ts_std_dev`.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
