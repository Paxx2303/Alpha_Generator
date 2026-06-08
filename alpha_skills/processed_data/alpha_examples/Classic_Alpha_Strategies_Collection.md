# Classic Alpha Strategies Collection

**Source:** Compiled from academic literature and industry practice 
**Focus:** Proven quantitative alpha strategies with empirical validation 
**Application:** Systematic trading and portfolio construction

## Overview

This collection presents time-tested alpha strategies that have demonstrated consistent performance across different market regimes. Each strategy includes mathematical formulation, implementation details, and performance characteristics.

## 1. Mean Reversion Strategies

### 1.1 Short-Term Reversal Alpha
**Concept:** Stocks that decline significantly tend to bounce back in the short term

**Formula:**
```
Alpha_STR = -1 * rank(returns_1d) * volatility_adjustment
```

**Implementation:**
```python
def short_term_reversal_alpha(returns_1d, volatility_20d):
 """
 Short-term reversal alpha based on daily returns
 
 Parameters:
 - returns_1d: 1-day returns
 - volatility_20d: 20-day rolling volatility
 """
 
 # Rank returns (lower rank = worse performance)
 return_ranks = returns_1d.rank(pct=True)
 
 # Volatility adjustment (higher vol = higher expected reversal)
 vol_adjustment = volatility_20d / volatility_20d.median()
 
 # Alpha signal (negative correlation with recent returns)
 alpha = -1 * return_ranks * vol_adjustment
 
 return alpha.rank(pct=True) - 0.5 # Center around 0
```

**Performance Characteristics:**
- **Holding Period:** 1-5 days
- **Turnover:** High (200-500% annually)
- **Sharpe Ratio:** 1.5-2.5 (before costs)
- **Capacity:** Limited due to high turnover

### 1.2 Bollinger Band Mean Reversion
**Concept:** Prices tend to revert to moving average after extreme moves

**Formula:**
```
Alpha_BB = (price - MA_20) / (2 * std_20)
Signal = -1 * tanh(Alpha_BB) # Bounded between -1 and 1
```

**Implementation:**
```python
def bollinger_mean_reversion(prices, window=20):
 """
 Bollinger Band mean reversion signal
 
 Parameters:
 - prices: Stock prices
 - window: Moving average window
 """
 
 # Calculate moving average and standard deviation
 ma = prices.rolling(window).mean()
 std = prices.rolling(window).std()
 
 # Bollinger Band position
 bb_position = (prices - ma) / (2 * std)
 
 # Mean reversion signal (stronger signal for extreme positions)
 signal = -np.tanh(bb_position)
 
 return signal
```

## 2. Momentum Strategies

### 2.1 Cross-Sectional Momentum
**Concept:** Stocks with strong relative performance continue outperforming

**Formula:**
```
Alpha_CSM = rank(returns_12m_1m) * trend_strength * volatility_adjustment
```

**Implementation:**
```python
def cross_sectional_momentum(returns, formation_period=252, skip_period=21):
 """
 Cross-sectional momentum based on past returns
 
 Parameters:
 - returns: Daily returns
 - formation_period: Lookback period for momentum calculation
 - skip_period: Days to skip to avoid microstructure effects
 """
 
 # Calculate momentum (skip recent period)
 momentum = returns.rolling(formation_period).apply(
 lambda x: (1 + x[:-skip_period]).prod() - 1
 )
 
 # Trend strength (consistency of returns)
 trend_strength = returns.rolling(formation_period).apply(
 lambda x: np.sum(x > 0) / len(x)
 )
 
 # Volatility adjustment
 volatility = returns.rolling(formation_period).std()
 vol_adjustment = 1 / (1 + volatility)
 
 # Combined signal
 signal = momentum.rank(pct=True) * trend_strength * vol_adjustment
 
 return signal.rank(pct=True) - 0.5
```

### 2.2 Risk-Adjusted Momentum
**Concept:** Momentum adjusted for risk provides better risk-return profile

**Formula:**
```
Alpha_RAM = (returns_6m / volatility_6m) * consistency_factor
```

**Implementation:**
```python
def risk_adjusted_momentum(returns, window=126):
 """
 Risk-adjusted momentum using Sharpe ratio concept
 
 Parameters:
 - returns: Daily returns
 - window: Window for calculation (6 months ≈ 126 days)
 """
 
 # Calculate cumulative returns and volatility
 cum_returns = returns.rolling(window).apply(lambda x: (1 + x).prod() - 1)
 volatility = returns.rolling(window).std() * np.sqrt(252)
 
 # Risk-adjusted momentum (Sharpe-like ratio)
 risk_adj_momentum = cum_returns / volatility
 
 # Consistency factor (percentage of positive days)
 consistency = returns.rolling(window).apply(lambda x: np.mean(x > 0))
 
 # Combined signal
 signal = risk_adj_momentum * consistency
 
 return signal.rank(pct=True) - 0.5
```

## 3. Value Strategies

### 3.1 Earnings Yield Alpha
**Concept:** Stocks with high earnings relative to price tend to outperform

**Formula:**
```
Alpha_EY = rank(earnings_per_share / price) * quality_adjustment
```

**Implementation:**
```python
def earnings_yield_alpha(earnings_per_share, price, roe, debt_to_equity):
 """
 Earnings yield alpha with quality adjustment
 
 Parameters:
 - earnings_per_share: Trailing 12-month EPS
 - price: Current stock price
 - roe: Return on equity
 - debt_to_equity: Debt-to-equity ratio
 """
 
 # Basic earnings yield
 earnings_yield = earnings_per_share / price
 
 # Quality adjustment factors
 quality_score = (
 (roe > 0.15).astype(int) + # High ROE
 (debt_to_equity 0).astype(int) # Positive earnings
 ) / 3
 
 # Adjusted earnings yield
 adjusted_ey = earnings_yield * (0.5 + quality_score)
 
 return adjusted_ey.rank(pct=True) - 0.5
```

### 3.2 Book-to-Market with Growth
**Concept:** Value stocks with reasonable growth prospects

**Formula:**
```
Alpha_BMG = rank(book_value / market_cap) * growth_quality * financial_strength
```

**Implementation:**
```python
def book_to_market_growth(book_value, market_cap, revenue_growth, 
 earnings_growth, current_ratio):
 """
 Book-to-market alpha adjusted for growth and financial strength
 
 Parameters:
 - book_value: Book value of equity
 - market_cap: Market capitalization
 - revenue_growth: Revenue growth rate
 - earnings_growth: Earnings growth rate
 - current_ratio: Current assets / current liabilities
 """
 
 # Basic book-to-market ratio
 btm = book_value / market_cap
 
 # Growth quality (positive but not excessive growth)
 growth_quality = (
 ((revenue_growth > 0) & (revenue_growth 0) & (earnings_growth 0), axis=1
 )
 
 # Trend improvement (recent vs. historical profitability)
 recent_prof = (roe + roa + profit_margin) / 3
 historical_prof = earnings_history.mean(axis=1)
 trend_improvement = (recent_prof > historical_prof).astype(int)
 
 # Combined signal
 signal = profitability_score * consistency * (0.5 + 0.5 * trend_improvement)
 
 return signal.rank(pct=True) - 0.5
```

### 4.2 Financial Strength Alpha
**Concept:** Companies with strong balance sheets outperform during stress periods

**Formula:**
```
Alpha_FS = rank(current_ratio * (1 - debt_ratio) * interest_coverage)
```

**Implementation:**
```python
def financial_strength_alpha(current_ratio, debt_to_assets, interest_coverage,
 cash_to_assets, working_capital_to_assets):
 """
 Financial strength alpha based on balance sheet metrics
 
 Parameters:
 - current_ratio: Current assets / current liabilities
 - debt_to_assets: Total debt / total assets
 - interest_coverage: EBIT / interest expense
 - cash_to_assets: Cash / total assets
 - working_capital_to_assets: Working capital / total assets
 """
 
 # Individual strength components
 liquidity_score = np.minimum(current_ratio / 2, 1) # Cap at 1
 leverage_score = 1 - debt_to_assets # Lower debt = higher score
 coverage_score = np.minimum(interest_coverage / 10, 1) # Cap at 1
 cash_score = cash_to_assets
 working_capital_score = np.maximum(working_capital_to_assets, 0)
 
 # Combined financial strength
 financial_strength = (
 liquidity_score * 0.25 +
 leverage_score * 0.25 +
 coverage_score * 0.20 +
 cash_score * 0.15 +
 working_capital_score * 0.15
 )
 
 return financial_strength.rank(pct=True) - 0.5
```

## 5. Technical Analysis Alphas

### 5.1 RSI Divergence Alpha
**Concept:** Divergence between price and RSI indicates potential reversal

**Formula:**
```
Alpha_RSI = sign(price_trend) * sign(rsi_trend) * (-1) * |rsi - 50|/50
```

**Implementation:**
```python
def rsi_divergence_alpha(prices, window=14, divergence_window=20):
 """
 RSI divergence alpha signal
 
 Parameters:
 - prices: Stock prices
 - window: RSI calculation window
 - divergence_window: Window for trend comparison
 """
 
 # Calculate RSI
 delta = prices.diff()
 gain = (delta.where(delta > 0, 0)).rolling(window).mean()
 loss = (-delta.where(delta 0.15).astype(int) * 0.4 +
 (debt_to_equity 1.5).astype(int) * 0.3
 )
 
 # Growth score (0 to 1, penalize negative or excessive growth)
 growth_score = np.where(
 (revenue_growth > 0) & (revenue_growth 1 else 0
 )
 
 # Combined signal (stronger when persistence is low)
 signal = vol_reversion * (1 - np.abs(vol_persistence))
 
 return signal.rank(pct=True) - 0.5
```

### 8.2 Volatility Risk Premium Alpha
**Concept:** Implied volatility typically exceeds realized volatility

**Formula:**
```
Alpha_VRP = (implied_vol - realized_vol) / implied_vol * term_structure_slope
```

**Implementation:**
```python
def volatility_risk_premium_alpha(implied_vol, returns, window=30):
 """
 Volatility risk premium alpha
 
 Parameters:
 - implied_vol: Implied volatility from options
 - returns: Stock returns for realized volatility
 - window: Window for realized volatility calculation
 """
 
 # Calculate realized volatility
 realized_vol = returns.rolling(window).std() * np.sqrt(252)
 
 # Volatility risk premium
 vol_risk_premium = (implied_vol - realized_vol) / implied_vol
 
 # Term structure slope (if available)
 # Proxy: use volatility of volatility
 vol_of_vol = implied_vol.rolling(window).std()
 term_structure_proxy = vol_of_vol / implied_vol
 
 # Combined signal
 signal = vol_risk_premium * (1 + term_structure_proxy)
 
 return signal.rank(pct=True) - 0.5
```

## 9. Earnings and Fundamental Alphas

### 9.1 Earnings Surprise Alpha
**Concept:** Stocks with positive earnings surprises continue outperforming

**Formula:**
```
Alpha_ES = (actual_eps - expected_eps) / |expected_eps| * revision_momentum
```

**Implementation:**
```python
def earnings_surprise_alpha(actual_eps, expected_eps, analyst_revisions):
 """
 Earnings surprise alpha with revision momentum
 
 Parameters:
 - actual_eps: Actual reported EPS
 - expected_eps: Analyst consensus EPS estimate
 - analyst_revisions: Recent changes in analyst estimates
 """
 
 # Basic earnings surprise
 surprise = (actual_eps - expected_eps) / np.abs(expected_eps)
 
 # Revision momentum (recent changes in estimates)
 revision_momentum = analyst_revisions.rolling(60).mean() # 3-month average
 
 # Surprise magnitude (larger surprises have more impact)
 surprise_magnitude = np.abs(surprise)
 
 # Combined signal
 signal = surprise * (1 + revision_momentum) * (1 + surprise_magnitude)
 
 return signal.rank(pct=True) - 0.5
```

### 9.2 Analyst Revision Alpha
**Concept:** Upward revisions in analyst estimates predict outperformance

**Formula:**
```
Alpha_AR = (current_estimate - previous_estimate) / previous_estimate * breadth
```

**Implementation:**
```python
def analyst_revision_alpha(estimates_current, estimates_previous, 
 num_analysts, estimate_dispersion):
 """
 Analyst revision alpha
 
 Parameters:
 - estimates_current: Current analyst estimates
 - estimates_previous: Previous period estimates
 - num_analysts: Number of analysts covering stock
 - estimate_dispersion: Standard deviation of estimates
 """
 
 # Revision magnitude
 revision = (estimates_current - estimates_previous) / np.abs(estimates_previous)
 
 # Analyst breadth (more analysts = more reliable)
 breadth_factor = np.minimum(num_analysts / 10, 1) # Cap at 1
 
 # Consensus strength (lower dispersion = stronger consensus)
 consensus_strength = 1 / (1 + estimate_dispersion / np.abs(estimates_current))
 
 # Combined signal
 signal = revision * breadth_factor * consensus_strength
 
 return signal.rank(pct=True) - 0.5
```

## 10. Implementation Framework

### 10.1 Alpha Combination Engine
```python
class AlphaCombinationEngine:
 """
 Framework for combining multiple alpha signals
 """
 
 def __init__(self, alphas, lookback_window=252):
 self.alphas = alphas
 self.lookback_window = lookback_window
 self.weights = None
 
 def calculate_optimal_weights(self, returns):
 """
 Calculate optimal weights using mean-variance optimization
 """
 
 # Calculate alpha returns (assuming alphas are investable)
 alpha_returns = pd.DataFrame()
 for name, alpha in self.alphas.items():
 alpha_returns[name] = alpha.shift(1) * returns # Lag alpha by 1 period
 
 # Rolling covariance matrix
 cov_matrix = alpha_returns.rolling(self.lookback_window).cov()
 
 # Rolling mean returns
 mean_returns = alpha_returns.rolling(self.lookback_window).mean()
 
 # Optimize weights (equal risk contribution)
 weights = {}
 for date in alpha_returns.index[self.lookback_window:]:
 cov = cov_matrix.loc[date]
 mu = mean_returns.loc[date]
 
 # Equal risk contribution weights
 inv_vol = 1 / np.sqrt(np.diag(cov))
 w = inv_vol / np.sum(inv_vol)
 
 weights[date] = w
 
 self.weights = pd.DataFrame(weights).T
 return self.weights
 
 def combine_alphas(self, date):
 """
 Combine alphas using optimal weights
 """
 
 if self.weights is None:
 raise ValueError("Must calculate weights first")
 
 combined_alpha = 0
 for i, (name, alpha) in enumerate(self.alphas.items()):
 weight = self.weights.iloc[-1, i] # Use latest weights
 combined_alpha += weight * alpha.loc[date]
 
 return combined_alpha
```

### 10.2 Performance Attribution Framework
```python
def alpha_performance_attribution(alpha_signals, returns, benchmark_returns):
 """
 Comprehensive performance attribution for alpha strategies
 
 Parameters:
 - alpha_signals: Dictionary of alpha signals
 - returns: Stock returns
 - benchmark_returns: Benchmark returns
 """
 
 results = {}
 
 for name, alpha in alpha_signals.items():
 # Calculate strategy returns
 strategy_returns = alpha.shift(1) * returns
 
 # Performance metrics
 total_return = (1 + strategy_returns).prod() - 1
 volatility = strategy_returns.std() * np.sqrt(252)
 sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
 
 # Risk metrics
 max_drawdown = (strategy_returns.cumsum() - strategy_returns.cumsum().expanding().max()).min()
 
 # Alpha vs benchmark
 excess_returns = strategy_returns - benchmark_returns
 alpha_vs_benchmark = excess_returns.mean() * 252
 tracking_error = excess_returns.std() * np.sqrt(252)
 information_ratio = alpha_vs_benchmark / tracking_error
 
 results[name] = {
 'total_return': total_return,
 'volatility': volatility,
 'sharpe_ratio': sharpe_ratio,
 'max_drawdown': max_drawdown,
 'alpha_vs_benchmark': alpha_vs_benchmark,
 'information_ratio': information_ratio
 }
 
 return pd.DataFrame(results).T
```

## Conclusion

This collection of classic alpha strategies provides a comprehensive foundation for quantitative investment research. Each strategy has been validated through academic research and practical implementation, offering different risk-return profiles and market exposures.

### Key Implementation Principles
1. **Signal Combination:** Combine multiple alphas for enhanced risk-adjusted returns
2. **Risk Management:** Monitor factor exposures and correlation changes
3. **Transaction Costs:** Account for implementation costs in strategy evaluation
4. **Regime Awareness:** Adapt strategies to changing market conditions
5. **Continuous Research:** Regularly update and refine alpha signals

### Performance Expectations
- **Individual Alphas:** Sharpe ratios of 0.5-2.0 before costs
- **Combined Alphas:** Sharpe ratios of 1.0-3.0 through diversification
- **Capacity:** Varies by strategy, from $100M to $10B+
- **Decay:** Monitor for signal decay due to crowding

These strategies form the building blocks for sophisticated quantitative investment systems and provide a starting point for developing proprietary alpha research.