# Prospect Theory: An Analysis of Decision under Risk

**Authors:** Daniel Kahneman, Amos Tversky  
**Publication:** Econometrica, Vol. 47, No. 2 (Mar., 1979), pp. 263-291  
**DOI:** 10.2307/1914185  
**Citation Count:** 70,000+ citations  
**Nobel Prize:** Daniel Kahneman, 2002 (Economics)

## Abstract

This paper presents a critique of expected utility theory as a descriptive model of decision making under risk, and develops an alternative model, called prospect theory. Choices among risky prospects exhibit several pervasive effects that are inconsistent with the basic tenets of utility theory. In particular, people underweight outcomes that are merely probable in comparison with outcomes that are obtained with certainty. This tendency, called the certainty effect, contributes to risk aversion in choices involving sure gains and to risk seeking in choices involving sure losses. In addition, people generally discard components that are shared by all prospects under consideration. This tendency, called the isolation effect, leads to inconsistent preferences when the same choice is presented in different forms. An alternative theory of choice is developed, in which value is assigned to gains and losses rather than to final assets and in which probabilities are replaced by decision weights. The main properties of the proposed value function are: (i) it is defined on deviations from the reference point; (ii) it is generally concave for gains and commonly convex for losses; (iii) it is steeper for losses than for gains. Decision weights are generally lower than the corresponding probabilities, except in the range of low probabilities. Overweighting of low probabilities may contribute to the attractiveness of both insurance and gambling.

## Core Principles of Prospect Theory

### 1. Reference Point Dependence
- **Key Insight:** People evaluate outcomes as gains or losses relative to a reference point, not absolute wealth levels
- **Implication:** The same outcome can be perceived differently depending on the reference point
- **Financial Application:** Investors' decisions depend on purchase price, not just current market value

### 2. Loss Aversion
- **Definition:** Losses loom larger than equivalent gains
- **Mathematical Form:** λ ≈ 2.25 (loss aversion coefficient)
- **Formula:** v(-x) = -λv(x) for x > 0
- **Behavioral Manifestation:** People require $2.25 gain to offset $1 loss

### 3. Diminishing Sensitivity
- **Gains:** Concave value function for gains (risk aversion)
- **Losses:** Convex value function for losses (risk seeking)
- **Mathematical Form:** 
  - v(x) = x^α for gains (α < 1)
  - v(-x) = -λ(-x)^β for losses (β < 1)

### 4. Probability Weighting
- **Overweighting:** Small probabilities are overweighted
- **Underweighting:** Moderate to high probabilities are underweighted
- **Certainty Effect:** Outcomes with certainty are overweighted relative to probable outcomes

## Mathematical Framework

### Value Function
The value function v(x) has the following properties:

```
v(x) = {
  x^α           if x ≥ 0 (gains)
  -λ(-x)^β      if x < 0 (losses)
}
```

**Parameters:**
- α ≈ 0.88 (concavity for gains)
- β ≈ 0.88 (convexity for losses)  
- λ ≈ 2.25 (loss aversion coefficient)

### Probability Weighting Function
The decision weight π(p) transforms objective probabilities:

```
π(p) = p^γ / (p^γ + (1-p)^γ)^(1/γ)
```

**Properties:**
- π(0) = 0, π(1) = 1
- π(p) < p for moderate to high probabilities
- π(p) > p for very low probabilities
- γ ≈ 0.61 (typical parameter value)

### Prospect Evaluation
A prospect (x₁, p₁; x₂, p₂; ...; xₙ, pₙ) is evaluated as:

```
V = Σᵢ π(pᵢ) × v(xᵢ)
```

## Experimental Evidence

### Classic Examples

#### 1. Certainty Effect
**Problem 1:**
- Option A: $3,000 with certainty
- Option B: $4,000 with 80% probability, $0 with 20% probability

**Result:** 80% choose A (risk aversion for gains)

**Problem 2:**
- Option C: -$3,000 with certainty  
- Option D: -$4,000 with 80% probability, $0 with 20% probability

**Result:** 92% choose D (risk seeking for losses)

#### 2. Isolation Effect
**Problem 3:**
- Stage 1: 75% chance to win $1,000, 25% chance to get nothing
- Stage 2 (if won Stage 1): Choose between $1,000 certain vs. 50% chance of $2,000

**Framing 1:** Most choose certain $1,000 in Stage 2
**Framing 2:** When presented as single choice, most prefer 50% chance of $2,000

#### 3. Reflection Effect
**Gains Domain:**
- 84% prefer $3,000 certain over 80% chance of $4,000

**Losses Domain:**  
- 69% prefer 80% chance of -$4,000 over -$3,000 certain

## Applications in Finance

### 1. Portfolio Theory Implications

#### Traditional vs. Prospect Theory
**Expected Utility Theory:**
- Investors maximize E[U(W)]
- Risk aversion throughout wealth domain
- Consistent risk preferences

**Prospect Theory:**
- Investors evaluate gains/losses from reference point
- Risk aversion for gains, risk seeking for losses
- Reference point determines behavior

#### Portfolio Construction Under Prospect Theory
```python
def prospect_utility(returns, reference_point=0, alpha=0.88, beta=0.88, lambda_loss=2.25):
    """
    Calculate prospect theory utility for portfolio returns
    
    Parameters:
    - returns: Array of portfolio returns
    - reference_point: Reference point for gains/losses
    - alpha: Concavity parameter for gains
    - beta: Convexity parameter for losses  
    - lambda_loss: Loss aversion coefficient
    """
    
    gains = returns - reference_point
    
    # Value function
    value = np.where(gains >= 0, 
                    gains ** alpha,
                    -lambda_loss * ((-gains) ** beta))
    
    return value
```

### 2. Asset Pricing Implications

#### Disposition Effect
- **Definition:** Tendency to sell winners too early and hold losers too long
- **Mechanism:** Loss aversion makes investors reluctant to realize losses
- **Evidence:** Documented across individual and institutional investors

#### Equity Premium Puzzle
- **Traditional Explanation:** High risk aversion (γ > 30)
- **Prospect Theory Explanation:** Loss aversion with narrow framing
- **Myopic Loss Aversion:** Frequent evaluation increases loss aversion impact

### 3. Market Anomalies Explained

#### Momentum Effect
- **Underreaction:** Investors underreact to news due to anchoring on reference points
- **Continuation:** Gradual adjustment leads to momentum
- **Reversal:** Long-term overreaction causes eventual reversal

#### Value Premium  
- **Loss Aversion:** Investors overpay for "safe" growth stocks
- **Reference Point:** Recent performance becomes reference point
- **Value Opportunity:** Distressed stocks undervalued due to loss aversion

## Behavioral Biases Derived from Prospect Theory

### 1. Mental Accounting
- **Definition:** Treating money differently based on source or intended use
- **Example:** Separate budgets for different categories
- **Investment Implication:** Suboptimal portfolio allocation

### 2. Endowment Effect
- **Definition:** Overvaluing items simply because you own them
- **Mechanism:** Loss aversion makes giving up ownership painful
- **Trading Implication:** Reduced trading volume, status quo bias

### 3. Framing Effects
- **Definition:** Decisions influenced by how options are presented
- **Example:** 90% survival rate vs. 10% mortality rate
- **Investment Implication:** Marketing affects investment choices

### 4. Probability Weighting Biases
- **Overconfidence:** Overweighting small probability of success
- **Insurance Demand:** Overweighting small probability of disaster
- **Lottery Preference:** Overweighting small probability of jackpot

## Empirical Evidence in Financial Markets

### 1. Individual Investor Behavior

#### Disposition Effect Studies
- **Odean (1998):** Individual investors 1.65x more likely to sell winners
- **Grinblatt & Keloharju (2001):** Finnish investors exhibit strong disposition effect
- **Feng & Seasholes (2005):** Disposition effect decreases with experience

#### Reference Point Studies
- **Kaustia (2010):** IPO reference points affect selling decisions
- **Arkes et al. (2008):** Purchase price serves as reference point
- **Weber & Camerer (1998):** Experimental evidence of reference dependence

### 2. Institutional Investor Behavior

#### Mutual Fund Studies
- **Coval & Shumway (2005):** Afternoon trading after morning losses
- **Kempf et al. (2014):** Fund managers increase risk after losses
- **Brown et al. (1996):** Tournament behavior in fund management

#### Hedge Fund Evidence
- **Agarwal et al. (2009):** Risk-taking increases after poor performance
- **Hodder & Jackwerth (2007):** Convex compensation creates loss aversion
- **Panageas & Westerfield (2009):** High-water marks and risk-taking

### 3. Market-Level Implications

#### Aggregate Market Behavior
- **Benartzi & Thaler (1995):** Myopic loss aversion explains equity premium
- **Barberis et al. (2001):** Prospect theory model of stock prices
- **Gomes (2005):** Loss aversion in general equilibrium

#### Cross-Sectional Asset Pricing
- **Barberis & Huang (2008):** Individual stock returns and prospect theory
- **De Giorgi & Legg (2012):** Prospect theory and momentum
- **Baele et al. (2019):** Volatility and prospect theory preferences

## Implementation in Quantitative Finance

### 1. Risk Management Applications

#### Value-at-Risk Extensions
```python
def prospect_var(returns, confidence_level=0.05, lambda_loss=2.25):
    """
    Calculate Prospect Theory adjusted VaR
    
    Accounts for loss aversion in risk measurement
    """
    
    var_traditional = np.percentile(returns, confidence_level * 100)
    
    # Adjust for loss aversion
    var_prospect = var_traditional * lambda_loss
    
    return var_prospect
```

#### Optimal Stopping Problems
- **Reference Point Evolution:** Dynamic reference point updating
- **Loss Realization:** Optimal timing for loss realization
- **Gain Taking:** Optimal profit-taking strategies

### 2. Portfolio Optimization

#### Prospect Theory Portfolio Model
```python
def optimize_prospect_portfolio(expected_returns, covariance_matrix, 
                               reference_point=0, alpha=0.88, beta=0.88, 
                               lambda_loss=2.25):
    """
    Optimize portfolio under prospect theory preferences
    
    Maximizes prospect theory utility instead of expected utility
    """
    
    def prospect_objective(weights):
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_variance = np.dot(weights, np.dot(covariance_matrix, weights))
        
        # Simulate returns and calculate prospect utility
        simulated_returns = np.random.normal(portfolio_return, 
                                           np.sqrt(portfolio_variance), 10000)
        
        gains = simulated_returns - reference_point
        
        utility = np.where(gains >= 0,
                          gains ** alpha,
                          -lambda_loss * ((-gains) ** beta))
        
        return -np.mean(utility)  # Negative for minimization
    
    # Optimization constraints
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = [(0, 1) for _ in range(len(expected_returns))]
    
    result = minimize(prospect_objective, 
                     x0=np.ones(len(expected_returns)) / len(expected_returns),
                     method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result.x
```

### 3. Algorithmic Trading Strategies

#### Reference Point Momentum
- **Strategy:** Exploit reference point anchoring
- **Implementation:** Identify stocks trading near reference points
- **Signal:** Momentum continuation from reference point breaks

#### Loss Aversion Arbitrage
- **Strategy:** Exploit disposition effect selling pressure
- **Implementation:** Buy stocks with recent losses, strong fundamentals
- **Signal:** Divergence between fundamental and technical indicators

## Criticisms and Limitations

### 1. Theoretical Criticisms

#### Descriptive vs. Normative
- **Issue:** Prospect theory describes behavior, doesn't prescribe optimal decisions
- **Implication:** May not be appropriate for institutional decision-making
- **Response:** Useful for understanding market behavior and inefficiencies

#### Parameter Stability
- **Issue:** Parameters (α, β, λ) may vary across individuals and contexts
- **Evidence:** Cultural differences in loss aversion
- **Implication:** Need for adaptive models

### 2. Empirical Challenges

#### Laboratory vs. Field
- **Issue:** Lab experiments may not reflect real-world decisions
- **Stakes:** Higher stakes may reduce behavioral biases
- **Experience:** Professional investors may exhibit less bias

#### Measurement Difficulties
- **Reference Points:** Difficult to identify in practice
- **Probability Weighting:** Complex to estimate from market data
- **Individual Differences:** Heterogeneity in parameters

### 3. Market Efficiency Implications

#### Learning and Arbitrage
- **Professional Investors:** May not exhibit prospect theory biases
- **Arbitrage:** Rational investors may exploit behavioral biases
- **Market Evolution:** Biases may diminish over time

#### Institutional Constraints
- **Fiduciary Duty:** Institutional investors have different objectives
- **Regulation:** Rules may prevent exploitation of biases
- **Competition:** Market forces may eliminate inefficiencies

## Modern Extensions and Applications

### 1. Cumulative Prospect Theory
- **Authors:** Tversky & Kahneman (1992)
- **Improvement:** Addresses violations of stochastic dominance
- **Application:** More robust for complex financial decisions

### 2. Behavioral Asset Pricing Models
- **Barberis-Huang Model:** Incorporates prospect theory into asset pricing
- **Habit Formation:** Reference points evolve with consumption history
- **Disappointment Aversion:** Alternative to loss aversion

### 3. Neuroeconomics Integration
- **Brain Imaging:** Neural correlates of prospect theory
- **Dopamine System:** Reward prediction errors and reference points
- **Individual Differences:** Genetic factors in risk preferences

## Practical Investment Applications

### 1. Retail Investment Products
- **Target-Date Funds:** Automatic reference point adjustment
- **Structured Products:** Exploit probability weighting biases
- **Robo-Advisors:** Behavioral coaching based on prospect theory

### 2. Institutional Investment Management
- **Risk Budgeting:** Incorporate loss aversion in risk allocation
- **Performance Evaluation:** Adjust for reference point effects
- **Client Communication:** Frame performance relative to goals

### 3. Financial Planning
- **Goal-Based Investing:** Multiple reference points for different goals
- **Retirement Planning:** Loss aversion in withdrawal strategies
- **Insurance Decisions:** Probability weighting in coverage choices

## Conclusion

Prospect Theory revolutionized our understanding of decision-making under risk and has profound implications for financial markets. By documenting systematic deviations from expected utility theory, Kahneman and Tversky provided a foundation for behavioral finance and explained numerous market anomalies.

### Key Contributions to Finance
1. **Market Anomalies:** Explains momentum, value premium, disposition effect
2. **Risk Management:** Loss aversion implications for risk measurement
3. **Portfolio Theory:** Alternative to mean-variance optimization
4. **Asset Pricing:** Behavioral factors in cross-sectional returns

### Ongoing Relevance
- **Algorithmic Trading:** Exploit behavioral biases systematically
- **Risk Management:** Incorporate behavioral factors in models
- **Product Design:** Create products aligned with behavioral preferences
- **Market Understanding:** Better comprehension of price formation

The theory continues to evolve with new applications in robo-advisory, ESG investing, and cryptocurrency markets, demonstrating its enduring relevance for understanding financial behavior.

## References

1. Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of decision under risk. Econometrica, 47(2), 263-291.

2. Tversky, A., & Kahneman, D. (1992). Advances in prospect theory: Cumulative representation of uncertainty. Journal of Risk and Uncertainty, 5(4), 297-323.

3. Barberis, N., & Huang, M. (2008). Stocks as lotteries: The implications of probability weighting for security prices. American Economic Review, 98(5), 2066-2100.

4. Benartzi, S., & Thaler, R. H. (1995). Myopic loss aversion and the equity premium puzzle. The Quarterly Journal of Economics, 110(1), 73-92.