# The Sharpe Ratio (Sharpe, 1994)

**Authors:** William F. Sharpe  
**Year:** 1994  
**Journal:** Journal of Portfolio Management  
**Topic:** Sharpe Ratio (Generalized Version)  

---

## 📝 Core Summary

William Sharpe updated and generalized his 1966 reward-to-variability ratio, officially naming it the **Sharpe Ratio**. In this paper, Sharpe generalized the formula to compare a portfolio's return to *any* benchmark portfolio (not just a risk-free asset). This generalized Sharpe ratio is mathematically equivalent to the Information Ratio when the benchmark is a risky index.

Key highlights:
- **Ex-Ante vs. Ex-Post:** Distinguished between the expected (ex-ante) Sharpe ratio used for portfolio construction and the realized (ex-post) Sharpe ratio used for historical performance measurement.
- **Scale Invariance:** The ratio is independent of leverage; borrowing or lending at the risk-free rate changes the returns and standard deviation proportionally, keeping the Sharpe ratio constant (assuming no lending spread).

---

## 🔢 Key Formulas

- **Generalized Sharpe Ratio (Ex-Post):**
  $$S = \frac{\bar{D}}{\sigma_D}$$

Where:
- $D_t = R_{pt} - R_{bt}$ is the differential return (portfolio return minus benchmark return) in period $t$.
- $\bar{D}$ is the average differential return over the period.
- $\sigma_D$ is the standard deviation of the differential returns.

---

## 💡 Application in WorldQuant Brain

Sharpe's 1994 update aligns perfectly with WQ Brain's simulation framework:

1. **Benchmark-Relative Evaluation:**
   Since WQ Brain portfolios are market-neutral, their returns are effectively "differential returns" ($D_t$) relative to the market benchmark ($R_m$). Therefore, the simulation Sharpe is exactly:
   $$\text{Simulation Sharpe} = \frac{\text{Mean of Daily Portfolio Returns}}{\text{StdDev of Daily Portfolio Returns}} \times \sqrt{252}$$
2. **Leverage/Scale Independence:**
   Because the Sharpe ratio is leverage-invariant, the WQ Brain simulation evaluates your formula's *relative ranks* rather than its absolute magnitude. The simulator automatically scales your raw weights to sum to 1 (or 100% exposure), meaning that scaling your formula by a constant (e.g. multiplying by 10) does not change the Sharpe ratio or the simulation result.

---

*Prepared as part of the Alpha Creator Skill research paper raw data package.*
