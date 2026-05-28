# Scalping

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A trading style specializing in taking profits on small price changes, holding positions for minutes or seconds.

---

## 🔢 Mathematical Formula

$$\text{Target Profit} < 1\% \text{ of price}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Extremely high turnover, very high transaction cost sensitivity.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
