# Market Neutral

**Category:** Trading Strategies & Concepts 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

An investment strategy that seeks to achieve zero correlation with the broader market, exploiting relative price moves.

---

## 🔢 Mathematical Formula

$$\beta_p = \sum w_i \beta_i = 0$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Mandatory in WQ Brain. Select 'Market' or 'Subindustry' neutralization in simulation settings.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*