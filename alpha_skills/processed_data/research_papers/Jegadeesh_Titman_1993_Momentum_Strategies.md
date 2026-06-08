# Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency

**Authors:** Narasimhan Jegadeesh, Sheridan Titman 
**Publication:** Journal of Finance, Vol. 48, No. 1 (Mar., 1993), pp. 65-91 
**DOI:** 10.1111/j.1540-6261.1993.tb04702.x 
**Citation Count:** 8,000+ citations 

## Abstract

This paper documents that strategies which buy stocks that have performed well in the past and sell stocks that have performed poorly in the past generate significant positive returns over 3- to 12-month holding periods. We find that the profitability of these strategies is not due to their systematic risk or to delayed stock price reactions to common factors. However, part of the abnormal returns generated in the first year after portfolio formation dissipates in the following two years. A similar pattern of returns is documented for portfolios formed on the basis of earnings momentum.

## Key Findings

### 1. Momentum Effect Discovery
- **Core Finding:** Stocks that performed well (poorly) in the past 3-12 months continue to perform well (poorly) in the subsequent 3-12 months
- **Statistical Significance:** Highly significant abnormal returns across all tested periods
- **Robustness:** Effect persists across different market conditions and time periods

### 2. Strategy Performance Metrics
- **Formation Period:** 3, 6, 9, and 12 months
- **Holding Period:** 3, 6, 9, and 12 months 
- **Best Performance:** 6-month formation, 6-month holding period
- **Average Monthly Return:** 1.31% for 6/6 strategy (15.7% annualized)
- **t-statistic:** 4.57 (highly significant)

### 3. Risk-Adjusted Returns
- **CAPM Alpha:** Significant positive alpha after adjusting for market beta
- **Systematic Risk:** Momentum profits not explained by systematic risk factors
- **Factor Analysis:** Returns not driven by size, book-to-market, or other known factors

## Methodology

### Portfolio Construction
1. **Ranking Period:** Sort stocks based on past J-month returns
2. **Portfolio Formation:** 
 - Winner Portfolio: Top 10% of stocks (highest past returns)
 - Loser Portfolio: Bottom 10% of stocks (lowest past returns)
3. **Strategy Implementation:** Long winners, short losers
4. **Rebalancing:** Monthly portfolio rebalancing
5. **Holding Period:** Hold positions for K months

### Data Specifications
- **Sample Period:** 1965-1989
- **Universe:** NYSE and AMEX stocks
- **Minimum Price:** $5 per share
- **Market Cap:** All sizes included
- **Exclusions:** REITs, closed-end funds, ADRs

### Statistical Tests
- **Significance Testing:** t-tests for abnormal returns
- **Risk Adjustment:** CAPM and multi-factor models
- **Robustness Checks:** Subperiod analysis, different formation periods

## Detailed Results

### Performance by Strategy (J/K months)
| Formation/Holding | Average Return | t-statistic | Sharpe Ratio |
|-------------------|----------------|-------------|--------------|
| 3/3 | 0.95% | 3.66 | 0.41 |
| 3/6 | 0.84% | 3.98 | 0.45 |
| 6/3 | 1.16% | 4.24 | 0.48 |
| 6/6 | 1.31% | 4.57 | 0.51 |
| 9/3 | 1.28% | 4.38 | 0.49 |
| 12/3 | 1.49% | 4.82 | 0.54 |

### Return Decomposition
- **Winner Portfolio:** Average monthly return of 1.73%
- **Loser Portfolio:** Average monthly return of 0.42%
- **Long-Short Spread:** 1.31% monthly (6/6 strategy)
- **Transaction Costs:** Estimated at 0.5% per trade

### Temporal Patterns
- **Immediate Momentum:** Strongest in months 2-6 after formation
- **Reversal Pattern:** Partial reversal in years 2-3 after formation
- **Seasonal Effects:** No significant seasonal patterns detected

## Risk Analysis

### Systematic Risk Factors
- **Market Beta:** Winner and loser portfolios have similar market betas
- **Size Effect:** Momentum profits exist within size quintiles
- **January Effect:** Momentum profits persist excluding January
- **Bid-Ask Spread:** Higher spreads for loser stocks, but profits remain significant

### Factor Loadings
- **Market Factor:** β ≈ 1.0 for long-short portfolio
- **Size Factor:** Small positive loading, not significant
- **Value Factor:** Slight growth tilt, but momentum profits independent

## Behavioral Explanations

### Underreaction Hypothesis
- **Delayed Response:** Markets underreact to firm-specific information
- **Information Diffusion:** Gradual incorporation of news into prices
- **Analyst Coverage:** Less coverage leads to slower price adjustment

### Overreaction vs. Underreaction
- **Short-term:** Underreaction dominates (momentum profits)
- **Long-term:** Overreaction emerges (reversal pattern)
- **Time Horizon:** Critical factor in determining effect direction

## Market Efficiency Implications

### Challenge to EMH
- **Weak-Form Efficiency:** Momentum profits violate weak-form efficiency
- **Predictability:** Past returns predict future returns
- **Arbitrage Limits:** Institutional constraints prevent arbitrage

### Rational Explanations
- **Risk Premium:** Time-varying risk premiums
- **Liquidity:** Compensation for liquidity provision
- **Transaction Costs:** Limits to arbitrage due to costs

## Implementation Considerations

### Trading Strategy
```python
# Momentum Strategy Implementation
def momentum_strategy(returns, formation_period=6, holding_period=6):
 """
 Implement Jegadeesh-Titman momentum strategy
 
 Parameters:
 - returns: DataFrame of stock returns
 - formation_period: Months for ranking (J)
 - holding_period: Months for holding (K)
 """
 
 # Calculate cumulative returns over formation period
 cum_returns = returns.rolling(formation_period).apply(
 lambda x: (1 + x).prod() - 1
 )
 
 # Rank stocks and form portfolios
 ranks = cum_returns.rank(axis=1, pct=True)
 
 # Long top decile, short bottom decile
 long_positions = (ranks >= 0.9).astype(int)
 short_positions = (ranks <= 0.1).astype(int) * -1
 
 # Combine positions
 positions = long_positions + short_positions
 
 # Calculate strategy returns
 strategy_returns = (positions.shift(1) * returns).sum(axis=1)
 
 return strategy_returns
```

### Risk Management
- **Position Sizing:** Equal-weighted portfolios
- **Rebalancing:** Monthly rebalancing to maintain exposure
- **Stop-Loss:** Not typically used in academic implementation
- **Leverage:** Typically implemented as dollar-neutral strategy

### Transaction Costs
- **Bid-Ask Spreads:** Higher for small-cap and loser stocks
- **Market Impact:** Significant for large institutional investors
- **Turnover:** High monthly turnover (≈50-100%)
- **Net Returns:** Gross returns minus estimated 2-4% annual costs

## Extensions and Variations

### International Evidence
- **Global Markets:** Momentum documented in 40+ countries
- **Emerging Markets:** Stronger momentum effects
- **Currency Effects:** Momentum in currency markets

### Asset Class Extensions
- **Fixed Income:** Bond momentum strategies
- **Commodities:** Commodity momentum
- **Options:** Momentum in implied volatility

### Factor Combinations
- **Value-Momentum:** Combining value and momentum factors
- **Quality-Momentum:** High-quality momentum stocks
- **Low-Vol Momentum:** Low-volatility momentum strategies

## Academic Impact

### Literature Development
- **Follow-up Studies:** 1,000+ papers citing this work
- **Factor Models:** Momentum as fourth factor (Carhart 1997)
- **Behavioral Finance:** Foundation for behavioral explanations

### Practical Applications
- **Mutual Funds:** Momentum-based fund strategies
- **Hedge Funds:** Systematic momentum strategies
- **ETFs:** Momentum factor ETFs launched

## Criticisms and Limitations

### Data Mining Concerns
- **Sample Period:** Limited to 1965-1989 in original study
- **Survivorship Bias:** Potential bias in stock selection
- **Look-Ahead Bias:** Careful construction to avoid bias

### Implementation Challenges
- **Capacity Constraints:** Strategy capacity limitations
- **Market Impact:** Price impact of large trades
- **Regime Changes:** Performance varies across market regimes

### Alternative Explanations
- **Risk-Based:** Time-varying risk premiums
- **Microstructure:** Bid-ask bounce effects
- **Data Quality:** Historical data limitations

## Modern Relevance

### Current Performance
- **Persistence:** Momentum effect continues post-1993
- **Decay:** Some evidence of declining profitability
- **Crowding:** Increased competition reduces returns

### Technology Impact
- **High-Frequency:** Intraday momentum strategies
- **Machine Learning:** AI-enhanced momentum models
- **Alternative Data:** News, social media momentum

### Regulatory Considerations
- **Short Selling:** Restrictions affect implementation
- **Market Making:** Impact on momentum profits
- **Algorithmic Trading:** Automated momentum strategies

## Conclusion

The Jegadeesh-Titman (1993) paper represents a watershed moment in financial economics, documenting one of the most robust and persistent market anomalies. The momentum effect challenges traditional notions of market efficiency and has spawned an entire literature on behavioral finance and factor investing.

### Key Contributions
1. **Empirical Discovery:** First systematic documentation of momentum
2. **Statistical Rigor:** Robust methodology and significance testing
3. **Economic Significance:** Large, persistent abnormal returns
4. **Theoretical Implications:** Challenge to efficient market hypothesis

### Lasting Impact
- **Academic Research:** Foundation for behavioral finance literature
- **Investment Practice:** Momentum strategies widely adopted
- **Risk Management:** Recognition of momentum as systematic risk factor
- **Market Understanding:** Enhanced understanding of price formation

The paper's methodology and findings continue to influence both academic research and practical investment management, making it one of the most important contributions to modern finance.

## References

1. Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. Journal of Finance, 48(1), 65-91.

2. Carhart, M. M. (1997). On persistence in mutual fund performance. Journal of Finance, 52(1), 57-82.

3. Fama, E. F., & French, K. R. (1996). Multifactor explanations of asset pricing anomalies. Journal of Finance, 51(1), 55-84.

4. Daniel, K., Hirshleifer, D., & Subrahmanyam, A. (1998). Investor psychology and security market under‐and overreactions. Journal of Finance, 53(6), 1839-1885.