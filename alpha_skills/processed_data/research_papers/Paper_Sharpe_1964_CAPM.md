# Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk (Sharpe, 1964)

**Authors:** William F. Sharpe 
**Year:** 1964 
**Journal:** Journal of Finance 
**Topic:** Capital Asset Pricing Model (CAPM) 

---

## 📝 Core Summary

William Sharpe built upon Markowitz's Modern Portfolio Theory to develop the **Capital Asset Pricing Model (CAPM)**. The paper demonstrates that in market equilibrium, the expected return on any asset is a linear function of its systematic risk (measured by Beta, $\beta$), which is the risk that cannot be diversified away. Diversifiable (idiosyncratic) risk is not rewarded by the market.

Key concepts introduced:
- **Systematic vs. Unsystematic Risk:** Systematic risk is market-wide and cannot be diversified. Unsystematic risk is company-specific and can be eliminated via diversification.
- **Security Market Line (SML):** The graphical representation of CAPM, showing expected asset returns as a function of systematic risk.

---

## 🔢 Key Formulas

- **CAPM Expected Return:**
 $$E(R_i) = R_f + \beta_i (E(R_m) - R_f)$$

- **Beta (Systematic Risk):**
 $$\beta_i = \frac{\text{Cov}(R_i, R_m)}{\text{Var}(R_m)}$$

Where:
- $R_f$ is the risk-free rate.
- $E(R_m)$ is the expected return of the market.
- $(E(R_m) - R_f)$ is the market risk premium.

---

## 💡 Application in WorldQuant Brain

CAPM defines the separation between market return (Beta) and active return (Alpha):

1. **Market-Beta Neutrality:**
 WQ Brain simulation requires alphas to be market-neutral. A market-neutral alpha ensures that the portfolio beta $\beta_p = 0$. By stripping out the market component ($R_m$), you ensure that the alpha's returns are purely idiosyncratic and not simply a reflection of market direction.
2. **Calculating Residual Returns (Idiosyncratic Returns):**
 You can construct alphas by modeling the residual returns after subtracting beta exposure:
 ```python
 // Proxy for residual price move: current price change minus market average price change
 market_mean = ts_mean(returns, 1); // average market return (proxy)
 residual_return = returns - market_mean;
 // Mean reversion on residual return
 signal = -rank(residual_return);
 rank(signal)
 ```

---

*Prepared as part of the Alpha Creator Skill research paper raw data package.*