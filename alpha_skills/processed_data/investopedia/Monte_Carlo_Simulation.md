# Monte Carlo Simulation

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A mathematical technique used to estimate the possible outcomes of an uncertain event by running thousands of random trials.

---

## 🔢 Mathematical Formula

$$\text{Outcome}_j = g(\Theta, \epsilon_j)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Used to stress-test trading systems under various artificial market conditions.

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*