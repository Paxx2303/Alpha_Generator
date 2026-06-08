# Long Short Equity

**Category:** Trading Strategies & Concepts 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An investment strategy that takes long positions in stocks that are expected to rise and short positions in stocks expected to fall.

---

## 🔢 Mathematical Formula

$$\text{Net Exposure} = \sum w_{\text{long}} - \sum |w_{\text{short}}|$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

The standard structure of WQ Brain alphas, which go long top-ranked stocks and short bottom-ranked stocks.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*