# Efficient Capital Markets: A Review of Theory and Empirical Work (Fama, 1970)

**Authors:** Eugene F. Fama 
**Year:** 1970 
**Journal:** Journal of Finance 
**Topic:** Efficient Market Hypothesis (EMH) 

---

## 📝 Core Summary

Eugene F. Fama formalized the **Efficient Market Hypothesis (EMH)**, which states that stock prices fully reflect all available information, making it impossible to consistently achieve returns exceeding average market returns on a risk-adjusted basis.

Fama defined three levels of market efficiency:
1. **Weak-Form Efficiency:** Prices reflect all historical trading data (past prices, volume). Technical analysis cannot generate alpha.
2. **Semi-Strong Form Efficiency:** Prices reflect all publicly available information (earnings announcements, annual reports, news). Fundamental analysis cannot generate alpha.
3. **Strong-Form Efficiency:** Prices reflect all public and private (insider) information. No one can generate consistent alpha.

---

## 🔢 Joint Hypothesis Problem

Fama noted that tests of market efficiency are always joint tests of market efficiency and the underlying asset pricing model (e.g., CAPM). If an anomaly (excess return) is found, it could mean the market is inefficient, or it could mean the asset pricing model is incorrect (underestimating risk).

---

## 💡 Application in WorldQuant Brain

Alpha generation is essentially the search for market inefficiencies (anomalies) that violate weak or semi-strong form EMH:

1. **Weak-Form Violations (Price-Volume Alphas):**
 Utilizing past prices and volumes to trade (e.g., mean reversion, momentum, lead-lag effects). 
 WQ Brain Example: Exploiting lag in information dissemination:
 ```python
 // Reversion on short-term price extreme
 signal = -rank(ts_delta(close, 5));
 rank(signal)
 ```
2. **Semi-Strong Form Violations (Fundamental Alphas):**
 Utilizing company fundamentals (P/E, earnings, news sentiment) before the market fully discounts them:
 ```python
 // Buying cheap companies with growing earnings
 cheapness = rank(-ts_backfill(pe));
 growth = rank(ts_delta(ebitda, 252));
 signal = cheapness + growth;
 rank(signal)
 ```

---

*Prepared as part of the Alpha Creator Skill research paper raw data package.*