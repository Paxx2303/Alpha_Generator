# Random Walk

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A financial theory stating that stock market prices evolve according to a random walk and thus cannot be predicted.

---

## 🔢 Mathematical Formula

$$P_t = P_{t-1} + \epsilon_t$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Efficient Market Hypothesis baseline. Alpha researchers aim to exploit deviations from random walk.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*