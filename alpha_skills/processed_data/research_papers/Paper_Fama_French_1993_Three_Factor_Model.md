# Common Risk Factors in the Returns on Stocks and Bonds (Fama & French, 1993)

**Authors:** Eugene F. Fama & Kenneth R. French 
**Year:** 1993 
**Journal:** Journal of Financial Economics 
**Topic:** Multi-Factor Models 

---

## 📝 Core Summary

Fama and French expanded the single-factor CAPM by introducing the **Three-Factor Model**. They demonstrated that stock returns are explained by three risk factors: market risk, size risk (Small Minus Big), and value risk (High Minus Low). This model significantly increased the explanation of stock return variance from CAPM's ~70% to over 90%.

The three factors are:
1. **Market Risk (MKT):** The return of the market portfolio minus the risk-free rate.
2. **Size Factor (SMB - Small Minus Big):** The historic excess returns of small-cap stocks over large-cap stocks.
3. **Value Factor (HML - High Minus Low):** The historic excess returns of value stocks (high book-to-market ratio) over growth stocks (low book-to-market).

---

## 🔢 Key Formulas

- **Fama-French Three-Factor Equation:**
 $$R_{it} - R_{ft} = \alpha_i + \beta_{i1} (R_{mt} - R_{ft}) + \beta_{i2} \text{SMB}_t + \beta_{i3} \text{HML}_t + \epsilon_{it}$$

Where:
- $\beta_{i1}$, $\beta_{i2}$, $\beta_{i3}$ are the portfolio's factor loadings (sensitivities) to the market, size, and value factors respectively.
- $\alpha_i$ is the unexplained excess return (the factor-adjusted Alpha).

---

## 💡 Application in WorldQuant Brain

Alphas in WQ Brain should target pure alpha ($\alpha_i$) by neutralizing exposure to known systemic risk factors (like size and value/fundamental sectors):

1. **Fundamental Value Factor Alpha (HML Proxy):**
 Replicate the value factor cross-sectionally:
 ```python
 // Buy stocks with high book-to-price ratios (value) and short low book-to-price (growth)
 value_factor = rank(book_value / close);
 signal = value_factor;
 rank(signal)
 ```
2. **Neutralizing Style Exposure:**
 To ensure your alpha is not just loading on the Fama-French SMB or HML factors, apply group neutralization. Neutralizing your value signal by Subindustry removes sector/industry specific beta, leaving pure stock-specific alpha:
 ```python
 raw_value = book_value / close;
 // Neutralize within subindustry to remove industry-wide value factor loadings
 signal = group_neutralize(raw_value, subindustry);
 rank(signal)
 ```

---

*Prepared as part of the Alpha Creator Skill research paper raw data package.*