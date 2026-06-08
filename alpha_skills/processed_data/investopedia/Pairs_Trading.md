# Pairs Trading

**Category:** Trading Strategies & Concepts 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A market-neutral trading strategy matching a long position in one asset with a short position in a highly correlated asset.

---

## 🔢 Mathematical Formula

$$\text{Spread} = \ln(P_A) - \ln(P_B)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Simplest stat-arb. WQ Brain: ranking assets within industry groups is equivalent to multi-pair relative trading.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*