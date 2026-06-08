# Win Rate

**Category:** Risk & Performance Metrics 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

The percentage of winning trades out of the total number of trades executed.

---

## 🔢 Mathematical Formula

$$\text{Win Rate} = \frac{\text{Winning Trades}}{\text{Total Trades}} \times 100$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

High win rate is psychologically satisfying, but profitability also depends on Risk-Reward Ratio.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*