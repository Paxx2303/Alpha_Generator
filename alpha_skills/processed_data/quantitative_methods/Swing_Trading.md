# Swing Trading

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A speculative strategy where an asset is held for between one to several days to profit from price swings.

---

## 🔢 Mathematical Formula

$$\text{Hold Period} \in [1, 10] \text{ days}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Most WQ Brain alphas fall here, capitalizing on short-term weekly or bi-weekly price swings.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
