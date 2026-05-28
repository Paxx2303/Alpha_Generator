# Common Risk Factors in the Returns on Stocks and Bonds

**Authors:** Eugene F. Fama, Kenneth R. French  
**Publication:** Journal of Financial Economics, Vol. 33, No. 1 (Feb., 1993), pp. 3-56  
**DOI:** 10.1016/0304-405X(93)90023-5  
**Citation Count:** 25,000+ citations  
**Nobel Prize:** Eugene Fama, 2013 (Economics)

## Abstract

This paper identifies five common risk factors in the returns on stocks and bonds. There are three stock-market factors: an overall market factor and factors related to firm size and book-to-market equity. There are two bond-market factors, related to maturity and default risks. Stock returns have shared variation due to the stock-market factors, and they are not exposed to the bond-market factors. Bond returns have shared variation due to the bond-market factors, and they show no sensitivity to the stock-market factors, except for low-grade corporates. The results suggest that the bond-market factors capture the systematic parts of the default and term premiums in bond returns.

## Introduction and Motivation

### Market Efficiency and Factor Models
The Fama-French research program aims to understand the cross-section of expected returns through factor models that capture systematic risk. This paper extends the Capital Asset Pricing Model (CAPM) by identifying additional risk factors that explain return variations not captured by market beta alone.

### Empirical Anomalies Addressed
- **Size Effect:** Small-cap stocks earn higher risk-adjusted returns
- **Value Effect:** High book-to-market stocks outperform growth stocks  
- **CAPM Failures:** Market beta alone insufficient to explain cross-sectional returns
- **Bond Market Factors:** Need for systematic factors in fixed income

## The Three-Factor Model for Stocks

### Factor Construction

#### 1. Market Factor (Rm - Rf)
- **Definition:** Excess return on value-weighted market portfolio
- **Proxy:** CRSP value-weighted index minus Treasury bill rate
- **Interpretation:** Systematic market risk affecting all stocks

#### 2. Size Factor (SMB - Small Minus Big)
- **Construction:** 
  - Sort stocks by market capitalization (NYSE breakpoints)
  - SMB = Average return of small-cap portfolios - Average return of large-cap portfolios
- **Interpretation:** Risk factor related to firm size

#### 3. Value Factor (HML - High Minus Low)
- **Construction:**
  - Sort stocks by book-to-market ratio (NYSE breakpoints)
  - HML = Average return of high B/M portfolios - Average return of low B/M portfolios  
- **Interpretation:** Risk factor related to book-to-market equity

### Portfolio Construction Methodology

#### Size-B/M Portfolios (2×3 Sort)
1. **Size Breakpoint:** NYSE median market cap
2. **B/M Breakpoints:** NYSE 30th and 70th percentiles
3. **Six Portfolios:** 
   - Small Value (SV), Small Neutral (SN), Small Growth (SG)
   - Big Value (BV), Big Neutral (BN), Big Growth (BG)

#### Factor Calculations
```
SMB = (SV + SN + SG)/3 - (BV + BN + BG)/3
HML = (SV + BV)/2 - (SG + BG)/2
```

### Three-Factor Model Specification
```
R(i,t) - RF(t) = α(i) + β(i)[RM(t) - RF(t)] + s(i)SMB(t) + h(i)HML(t) + ε(i,t)
```

**Where:**
- R(i,t) = Return on security or portfolio i in period t
- RF(t) = Risk-free rate in period t  
- RM(t) = Return on market portfolio in period t
- SMB(t) = Size factor return in period t
- HML(t) = Value factor return in period t
- β(i), s(i), h(i) = Factor loadings for security i
- α(i) = Abnormal return (intercept)
- ε(i,t) = Error term

## Empirical Results for Stock Returns

### Factor Performance Statistics (1963-1991)

#### Factor Returns and Volatilities
| Factor | Mean Return | Std Dev | t-statistic | Sharpe Ratio |
|--------|-------------|---------|-------------|--------------|
| Rm-Rf | 0.43% | 4.84% | 1.78 | 0.089 |
| SMB | 0.27% | 3.18% | 1.68 | 0.085 |
| HML | 0.40% | 2.91% | 2.74 | 0.137 |

#### Factor Correlations
|       | Rm-Rf | SMB | HML |
|-------|-------|-----|-----|
| Rm-Rf | 1.00  | 0.32| -0.07|
| SMB   | 0.32  | 1.00| -0.08|
| HML   | -0.07 | -0.08| 1.00|

### Size-B/M Portfolio Results

#### Average Monthly Returns (1963-1991)
|        | Low B/M | Med B/M | High B/M |
|--------|---------|---------|----------|
| Small  | 0.70%   | 1.05%   | 1.83%    |
| Big    | 0.65%   | 0.93%   | 1.18%    |

#### Three-Factor Alphas
|        | Low B/M | Med B/M | High B/M |
|--------|---------|---------|----------|
| Small  | -0.29%  | 0.11%   | 0.35%    |
| Big    | -0.17%  | 0.14%   | 0.08%    |

**Key Finding:** Three-factor model reduces abnormal returns (alphas) to statistically insignificant levels for most portfolios.

### Factor Loadings Analysis

#### Size Factor (SMB) Loadings
- **Small Stocks:** Positive loadings (0.8 to 1.2)
- **Large Stocks:** Negative loadings (-0.3 to -0.1)
- **Interpretation:** SMB captures size-related risk premium

#### Value Factor (HML) Loadings  
- **Value Stocks:** Positive loadings (0.3 to 1.0)
- **Growth Stocks:** Negative loadings (-0.2 to -0.5)
- **Interpretation:** HML captures value-related risk premium

## Bond Market Factors

### Two Bond Factors Identified

#### 1. Term Factor (TERM)
- **Construction:** Long-term government bond return minus Treasury bill return
- **Interpretation:** Captures interest rate risk and term structure effects
- **Average Return:** 0.21% monthly (t = 1.10)

#### 2. Default Factor (DEF)  
- **Construction:** Long-term corporate bond return minus long-term government bond return
- **Interpretation:** Captures default risk premium
- **Average Return:** 0.11% monthly (t = 1.69)

### Bond Portfolio Analysis

#### Government Bond Results
- **Sensitivity to TERM:** Strong positive loadings increase with maturity
- **Sensitivity to DEF:** Minimal exposure to default factor
- **Stock Factors:** No significant exposure to stock market factors

#### Corporate Bond Results
- **Investment Grade:** Positive DEF loadings, minimal stock exposure
- **High Yield:** Significant exposure to both bond and stock factors
- **Default Risk:** Higher DEF loadings for lower-rated bonds

## Five-Factor Model Integration

### Combined Stock-Bond Model
```
R(i,t) - RF(t) = α(i) + β(i)[RM(t) - RF(t)] + s(i)SMB(t) + h(i)HML(t) 
                 + t(i)TERM(t) + d(i)DEF(t) + ε(i,t)
```

### Cross-Asset Implications
- **Stock Returns:** Primarily driven by stock factors (Rm-Rf, SMB, HML)
- **Bond Returns:** Primarily driven by bond factors (TERM, DEF)
- **High-Yield Bonds:** Exposure to both stock and bond factors
- **Market Segmentation:** Limited cross-asset factor exposure

## Economic Interpretation

### Risk-Based Explanations

#### Size Factor (SMB)
- **Financial Distress:** Small firms more vulnerable to economic shocks
- **Information Asymmetry:** Less information available about small firms
- **Liquidity:** Small stocks less liquid, higher transaction costs
- **Operating Leverage:** Small firms more sensitive to business cycles

#### Value Factor (HML)
- **Financial Distress:** High B/M firms may face financial difficulties
- **Growth Options:** Low B/M firms have valuable growth opportunities
- **Systematic Risk:** Value stocks more sensitive to economic conditions
- **Mean Reversion:** Temporary mispricing corrects over time

#### Bond Factors
- **TERM Factor:** Compensation for interest rate risk
- **DEF Factor:** Compensation for default risk

### Behavioral Explanations
- **Overreaction:** Investors overreact to good/bad news
- **Extrapolation:** Excessive optimism/pessimism about growth
- **Risk Perception:** Systematic errors in risk assessment

## Model Performance and Validation

### Explanatory Power

#### R-squared Improvements
- **CAPM:** Average R² ≈ 0.70 for size-B/M portfolios
- **Three-Factor:** Average R² ≈ 0.95 for size-B/M portfolios
- **Improvement:** Substantial increase in explanatory power

#### Alpha Reduction
- **CAPM Alphas:** Many significant abnormal returns
- **Three-Factor Alphas:** Most alphas statistically insignificant
- **Economic Significance:** Alphas reduced from 0.5-1.0% to 0.1-0.3% monthly

### Robustness Tests

#### Subperiod Analysis
- **1963-1972:** Factors significant in early period
- **1973-1982:** Continued significance through different market regimes  
- **1983-1991:** Factors remain significant in recent period

#### Different Breakpoints
- **NYSE vs. All Stocks:** Results robust to breakpoint choice
- **Alternative Percentiles:** 20th/80th percentiles yield similar results
- **Annual Rebalancing:** Results consistent with different rebalancing frequencies

## Applications and Extensions

### Portfolio Management Applications

#### Factor-Based Investing
```python
def three_factor_portfolio_optimization(expected_returns, factor_loadings, 
                                      factor_covariance, idiosyncratic_risk):
    """
    Optimize portfolio using three-factor model
    
    Parameters:
    - expected_returns: Expected returns for assets
    - factor_loadings: Beta, SMB, HML loadings for each asset
    - factor_covariance: 3x3 covariance matrix of factors
    - idiosyncratic_risk: Asset-specific risk
    """
    
    def portfolio_risk(weights):
        # Factor risk contribution
        portfolio_loadings = np.dot(weights, factor_loadings)
        factor_risk = np.dot(portfolio_loadings, 
                           np.dot(factor_covariance, portfolio_loadings))
        
        # Idiosyncratic risk contribution  
        idio_risk = np.dot(weights**2, idiosyncratic_risk)
        
        return factor_risk + idio_risk
    
    def portfolio_return(weights):
        return np.dot(weights, expected_returns)
    
    # Optimization objective (maximize Sharpe ratio)
    def objective(weights):
        ret = portfolio_return(weights)
        risk = np.sqrt(portfolio_risk(weights))
        return -ret / risk  # Negative for minimization
    
    # Constraints and bounds
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = [(0, 1) for _ in range(len(expected_returns))]
    
    result = minimize(objective, 
                     x0=np.ones(len(expected_returns)) / len(expected_returns),
                     method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result.x
```

#### Risk Attribution
- **Factor Risk:** Decompose portfolio risk into factor components
- **Active Risk:** Measure deviations from factor benchmarks
- **Performance Attribution:** Separate alpha from factor exposures

### Academic Extensions

#### Four-Factor Model (Carhart 1997)
- **Momentum Factor:** UMD (Up Minus Down) based on past returns
- **Model:** Adds momentum to three-factor model
- **Improvement:** Better explains short-term return patterns

#### Five-Factor Model (Fama-French 2015)
- **Profitability Factor:** RMW (Robust Minus Weak) based on operating profitability
- **Investment Factor:** CMA (Conservative Minus Aggressive) based on asset growth
- **Evolution:** Addresses remaining anomalies in three-factor model

#### International Extensions
- **Global Factors:** Three-factor model applied internationally
- **Regional Factors:** Local vs. global factor importance
- **Currency Effects:** Additional factor for international portfolios

## Criticisms and Limitations

### Theoretical Criticisms

#### Lack of Economic Theory
- **Issue:** Factors identified empirically, not derived from theory
- **Response:** Factors may proxy for systematic risk sources
- **Alternative:** Consumption-based models provide theoretical foundation

#### Data Mining Concerns
- **Issue:** Factors may be result of extensive data searching
- **Evidence:** Out-of-sample performance supports factor validity
- **International Evidence:** Factors work globally, reducing data mining concerns

### Empirical Limitations

#### Factor Stability
- **Time Variation:** Factor premiums vary over time
- **Regime Changes:** Structural breaks in factor relationships
- **Sample Dependence:** Results may be sample-specific

#### Anomalies Remaining
- **Momentum:** Three-factor model doesn't explain momentum
- **Profitability:** Profitable firms outperform unprofitable firms
- **Investment:** Conservative firms outperform aggressive firms

### Practical Challenges

#### Implementation Costs
- **Transaction Costs:** Frequent rebalancing increases costs
- **Market Impact:** Large trades may move prices
- **Capacity Constraints:** Strategies may not scale

#### Factor Timing
- **Predictability:** Factor returns may be predictable
- **Market Timing:** Optimal factor exposure timing
- **Risk Management:** Managing factor concentration risk

## Modern Developments

### Machine Learning Applications
- **Factor Discovery:** ML techniques to identify new factors
- **Dynamic Models:** Time-varying factor loadings
- **Alternative Data:** Non-traditional data sources for factors

### ESG Integration
- **ESG Factors:** Environmental, social, governance factors
- **Sustainable Investing:** ESG-tilted factor portfolios
- **Impact Measurement:** ESG factor performance attribution

### High-Frequency Extensions
- **Intraday Factors:** Factor models for high-frequency data
- **Microstructure:** Market structure effects on factors
- **Real-Time Implementation:** Live factor exposure monitoring

## Practical Implementation Guide

### Factor Portfolio Construction

#### Step 1: Universe Definition
```python
def define_universe(market_cap_threshold=100e6, price_threshold=5.0):
    """
    Define investment universe for factor construction
    
    Parameters:
    - market_cap_threshold: Minimum market cap (USD)
    - price_threshold: Minimum share price (USD)
    """
    
    # Screen for liquid, investable stocks
    universe = stocks[
        (stocks['market_cap'] >= market_cap_threshold) &
        (stocks['price'] >= price_threshold) &
        (stocks['volume_20d_avg'] >= 1e6)  # Minimum liquidity
    ]
    
    return universe
```

#### Step 2: Factor Calculation
```python
def calculate_factors(returns_data, market_caps, book_values):
    """
    Calculate Fama-French factors
    
    Returns:
    - factor_returns: DataFrame with Rm-Rf, SMB, HML
    """
    
    # Market factor
    market_factor = returns_data.mean(axis=1) - risk_free_rate
    
    # Size breakpoint (NYSE median)
    size_breakpoint = market_caps[nyse_stocks].median()
    
    # B/M breakpoints (NYSE 30th, 70th percentiles)
    bm_ratios = book_values / market_caps
    bm_30 = bm_ratios[nyse_stocks].quantile(0.3)
    bm_70 = bm_ratios[nyse_stocks].quantile(0.7)
    
    # Form portfolios
    small = market_caps <= size_breakpoint
    big = market_caps > size_breakpoint
    value = bm_ratios >= bm_70
    neutral = (bm_ratios > bm_30) & (bm_ratios < bm_70)
    growth = bm_ratios <= bm_30
    
    # Calculate factor returns
    smb = (returns_data[small].mean(axis=1) - 
           returns_data[big].mean(axis=1))
    
    hml = ((returns_data[small & value].mean(axis=1) + 
            returns_data[big & value].mean(axis=1)) / 2 -
           (returns_data[small & growth].mean(axis=1) + 
            returns_data[big & growth].mean(axis=1)) / 2)
    
    return pd.DataFrame({
        'Rm-Rf': market_factor,
        'SMB': smb,
        'HML': hml
    })
```

#### Step 3: Factor Exposure Estimation
```python
def estimate_factor_loadings(asset_returns, factor_returns, window=60):
    """
    Estimate factor loadings using rolling regression
    
    Parameters:
    - asset_returns: Time series of asset returns
    - factor_returns: Time series of factor returns  
    - window: Rolling window length (months)
    """
    
    loadings = []
    
    for i in range(window, len(asset_returns)):
        y = asset_returns[i-window:i]
        X = factor_returns[i-window:i]
        X = sm.add_constant(X)  # Add intercept
        
        model = sm.OLS(y, X).fit()
        loadings.append(model.params[1:])  # Exclude intercept
    
    return pd.DataFrame(loadings, 
                       columns=['Beta', 'SMB_loading', 'HML_loading'],
                       index=asset_returns.index[window:])
```

### Performance Evaluation

#### Factor Model Diagnostics
```python
def factor_model_diagnostics(returns, factor_loadings, factor_returns):
    """
    Comprehensive factor model diagnostics
    
    Returns:
    - R-squared, alpha, factor significance tests
    """
    
    # Predicted returns
    predicted_returns = np.dot(factor_loadings, factor_returns.T)
    
    # Model fit statistics
    r_squared = 1 - np.var(returns - predicted_returns) / np.var(returns)
    
    # Alpha estimation
    alpha = np.mean(returns - predicted_returns)
    alpha_tstat = alpha / (np.std(returns - predicted_returns) / np.sqrt(len(returns)))
    
    # Factor significance
    factor_tstats = []
    for i, factor in enumerate(factor_returns.columns):
        factor_loading = factor_loadings[i]
        residuals = returns - predicted_returns
        se_loading = np.std(residuals) / (np.std(factor_returns[factor]) * np.sqrt(len(returns)))
        t_stat = factor_loading / se_loading
        factor_tstats.append(t_stat)
    
    return {
        'r_squared': r_squared,
        'alpha': alpha,
        'alpha_tstat': alpha_tstat,
        'factor_tstats': factor_tstats
    }
```

## Conclusion

The Fama-French three-factor model represents a landmark contribution to asset pricing theory and practice. By identifying size and value as systematic risk factors, the model provides a more complete explanation of cross-sectional return differences than the CAPM alone.

### Key Contributions
1. **Empirical Framework:** Systematic approach to factor identification
2. **Risk Explanation:** Size and value as compensation for systematic risk
3. **Practical Application:** Foundation for factor-based investing
4. **Academic Impact:** Spawned extensive literature on factor models

### Lasting Impact
- **Investment Management:** Factor investing becomes mainstream strategy
- **Risk Management:** Multi-factor risk models standard practice  
- **Academic Research:** Template for factor model development
- **Market Understanding:** Enhanced comprehension of return sources

The model continues to evolve with new factors and applications, demonstrating its fundamental importance for understanding financial markets and constructing investment strategies.

## References

1. Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and bonds. Journal of Financial Economics, 33(1), 3-56.

2. Fama, E. F., & French, K. R. (1992). The cross‐section of expected stock returns. Journal of Finance, 47(2), 427-465.

3. Carhart, M. M. (1997). On persistence in mutual fund performance. Journal of Finance, 52(1), 57-82.

4. Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. Journal of Financial Economics, 116(1), 1-22.