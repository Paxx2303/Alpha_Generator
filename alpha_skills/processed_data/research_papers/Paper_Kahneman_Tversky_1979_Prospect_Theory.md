# Prospect Theory: An Analysis of Decision under Risk (Kahneman & Tversky, 1979)

**Authors:** Daniel Kahneman & Amos Tversky 
**Year:** 1979 
**Journal:** Econometrica 
**Topic:** Behavioral Finance / Prospect Theory 

---

## 📝 Core Summary

This Nobel-winning paper laid the foundation for **Behavioral Finance**. Kahneman and Tversky challenged expected utility theory, demonstrating that real human beings evaluate gains and losses differently, making decisions based on perceived gains rather than final wealth.

Key concepts introduced:
- **Loss Aversion:** The psychological pain of a loss is about twice as intense as the pleasure of an equivalent gain. Humans are risk-averse when facing gains, but risk-seeking when facing losses (hoping to break even).
- **Disposition Effect:** Investors tend to sell winning stocks too early (to secure a gain) and hold onto losing stocks too long (hoping they recover).
- **Probability Distortion:** People overestimate small probabilities (lottery tickets) and underestimate medium-to-large probabilities.

---

## 🔢 Value Function

Prospect theory describes utility via an S-shaped value function:
- Concave for gains (risk aversion).
- Convex for losses (risk seeking).
- Steeper in the loss domain than in the gain domain (loss aversion).

$$V(x) = \begin{cases} x^\alpha & \text{if } x \ge 0 \\ -\lambda (-x)^\beta & \text{if } x < 0 \end{cases} \quad \text{where } \lambda \approx 2.25$$

---

## 💡 Application in WorldQuant Brain

Behavioral biases create predictable price patterns (anomalies) that quantitative alphas can exploit:

1. **Exploiting the Disposition Effect (Momentum):**
 Because investors sell winners too early, prices of winning stocks rise slower than they should, creating **momentum**. Alphas buy these rising stocks:
 ```python
 // Buy stocks with strong, stable 12-month momentum
 signal = rank(ts_delta(close, 252) / ts_std_dev(returns, 252));
 rank(signal)
 ```
2. **Exploiting Loss Aversion (Post-Earnings Announcement Drift - PEAD):**
 Underreaction to negative earnings news due to loss-averse investors holding on to losing stocks leads to prolonged downward drift. Alphas short these names:
 ```python
 // Short stocks with recent negative earnings surprises
 signal = -rank(ts_delta(eps, 252));
 rank(signal)
 ```

---

*Prepared as part of the Alpha Creator Skill research paper raw data package.*