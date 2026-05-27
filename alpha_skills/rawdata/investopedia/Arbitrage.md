# Arbitrage

**Category:** Trading Strategies & Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The simultaneous purchase and sale of an asset in different markets to exploit tiny price discrepancies and earn risk-free profits.

---

## 🔢 Mathematical Formula

$$\text{Profit} = P_{\text{Sell}} - P_{\text{Buy}} > 0 \text{ (Risk-Free)}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Locks in risk-free spreads (e.g. spot vs futures). Keeps markets efficient.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*
