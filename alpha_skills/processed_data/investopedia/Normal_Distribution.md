# Normal Distribution

**Category:** Quantitative & Statistical Analysis 
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

A probability distribution that is symmetric about the mean, showing that data near the mean are more frequent in occurrence.

---

## 🔢 Mathematical Formula

$$f(x) = \frac{1}{\sigma \sqrt{2\pi}} e^{-\frac{1}{2}\left(\frac{x-\mu}{\sigma}\right)^2}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Baseline assumption of Sharpe ratio. In practice, financial returns are fat-tailed (leptokurtic).

- **Neutralization Recommendation:** Typically, price-volume expressions under this concept should use **Market** neutralization to eliminate macro biases, while fundamental expressions can use **Subindustry** neutralization.
- **Tuning Tip:** If the turnover of an alpha built under this concept is too high (e.g. >70%), consider smoothing the final expression with `ts_decay_linear(signal, d)` where `d` is between 3 and 10.

---

*Prepared as part of the Alpha Creator Skill raw data package.*