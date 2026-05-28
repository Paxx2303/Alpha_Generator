# Portfolio Selection (Markowitz, 1952)

**Authors:** Harry Markowitz  
**Year:** 1952  
**Journal:** Journal of Finance  
**Topic:** Modern Portfolio Theory (MPT)  

---

## 📝 Core Summary

This foundational paper is the birth of **Modern Portfolio Theory (MPT)**. Markowitz mathematically demonstrated that investors can reduce portfolio risk through diversification by selecting assets that do not move in perfect lockstep (i.e., have low or negative correlation). He established the "Mean-Variance" framework, showing that asset allocation should focus on the trade-off between expected return and variance (risk) of the entire portfolio, rather than looking at individual assets in isolation.

Key concepts introduced:
- **Efficient Frontier:** The set of optimal portfolios that offer the highest expected return for a defined level of risk, or the lowest risk for a given level of expected return.
- **Diversification Benefit:** Portfolio variance depends not only on individual asset variances but also on the pairwise covariances between assets.

---

## 🔢 Key Formulas

- **Portfolio Expected Return:**
  $$E(R_p) = \sum_{i=1}^n w_i E(R_i) = w^T E(R)$$

- **Portfolio Variance:**
  $$\sigma_p^2 = \sum_{i=1}^n \sum_{j=1}^n w_i w_j \text{Cov}(R_i, R_j) = w^T \Sigma w$$

Where:
- $w$ is the vector of portfolio weights.
- $\Sigma$ is the covariance matrix of asset returns.

---

## 💡 Application in WorldQuant Brain

Markowitz's variance-reduction principles are embedded in the risk constraints of WorldQuant Brain simulations:

1. **Pasteurization & Truncation:** 
   WQ Brain automatically applies weight truncation (maximum weight for a single stock, e.g., 0.05 or 0.10) to prevent concentration risk, aligning with MPT's push for diversification.
2. **Neutralization as Covariance Control:**
   Statistical and sector neutralization (`group_neutralize` or choosing Subindustry/Market neutralization) actively strips out industry-wide systemic covariance, leaving the portfolio exposed only to idiosyncratic, uncorrelated alpha returns, which greatly enhances the Sharpe ratio.

---

*Prepared as part of the Alpha Creator Skill research paper raw data package.*
