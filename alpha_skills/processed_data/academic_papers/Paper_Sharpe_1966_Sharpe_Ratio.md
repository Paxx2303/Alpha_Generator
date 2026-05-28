# Mutual Fund Performance (Sharpe, 1966)

**Authors:** William F. Sharpe  
**Year:** 1966  
**Journal:** Journal of Business  
**Topic:** Sharpe Ratio (Reward-to-Variability Ratio)  

---

## 📝 Core Summary

In this paper, William Sharpe introduced the "reward-to-variability ratio" (later named the **Sharpe Ratio**) to evaluate the performance of mutual funds. Sharpe argued that evaluating mutual funds based on raw returns is insufficient; performance must be adjusted for total risk (standard deviation of returns). The Sharpe Ratio measures the excess return per unit of total volatility.

Key concepts introduced:
- **Reward-to-Variability Ratio:** The excess return of a fund over the risk-free rate, divided by the standard deviation of the fund's returns.
- **Risk-Adjusted Performance Ranking:** Allows comparing funds with different risk profiles on a fair, standardized scale.

---

## 🔢 Key Formulas

- **Sharpe Ratio:**
  $$\text{Sharpe Ratio} = \frac{R_p - R_f}{\sigma_p}$$

Where:
- $R_p$ is the annualized return of the portfolio.
- $R_f$ is the annualized risk-free rate.
- $\sigma_p$ is the annualized standard deviation of the portfolio's excess returns.

---

## 💡 Application in WorldQuant Brain

The Sharpe Ratio is the primary fitness metric in WorldQuant Brain:

1. **Required Sharpe (>1.25):** 
   All submitted alphas must have a simulation Sharpe ratio of at least 1.25.
2. **Improving Sharpe in Alpha Design:**
   According to the formula, to maximize Sharpe, you must:
   - **Increase $R_p$:** Enhance signal predictability.
   - **Decrease $\sigma_p$:** Remove volatility spikes. You can achieve this by using the `winsorize(signal, threshold)` or `zscore(signal)` operators to clip outliers, preventing single stocks from creating massive, volatile swings in portfolio returns.

---

*Prepared as part of the Alpha Creator Skill research paper raw data package.*
