# Risk Parity and Factor Investing Strategies

**Focus:** Modern portfolio construction techniques beyond traditional mean-variance optimization  
**Applications:** Institutional portfolio management, factor-based investing, risk budgeting  
**Key Concepts:** Risk parity, factor investing, smart beta, alternative risk premia

## Overview

Risk parity and factor investing represent significant advances in portfolio construction methodology, moving beyond traditional market-cap weighted approaches to focus on risk-based allocation and systematic factor exposures. These strategies aim to improve risk-adjusted returns through more efficient diversification and systematic capture of risk premia.

## 1. Risk Parity Fundamentals

### 1.1 Core Principles
**Equal Risk Contribution:** Each asset contributes equally to portfolio risk
**Diversification Focus:** Maximize diversification benefits across risk sources
**Risk-Based Allocation:** Weights determined by risk characteristics, not expected returns

### Mathematical Framework
**Risk Contribution Formula:**
```
RC_i = w_i * (Σw)_i / σ_p
```

Where:
- RC_i = Risk contribution of asset i
- w_i = Weight of asset i
- (Σw)_i = i-th element of covariance matrix times weight vector
- σ_p = Portfolio volatility

### 1.2 Equal Risk Contribution (ERC) Portfolio
**Objective:** Minimize sum of squared differences in risk contributions

```python
import numpy as np
from scipy.optimize import minimize

def equal_risk_contribution_portfolio(cov_matrix):
    """
    Calculate Equal Risk Contribution portfolio weights
    
    Parameters:
    - cov_matrix: Asset covariance matrix
    
    Returns:
    - weights: Optimal portfolio weights
    """
    
    n_assets = cov_matrix.shape[0]
    
    def risk_contributions(weights, cov_matrix):
        """Calculate risk contributions for each asset"""
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
        risk_contrib = weights * marginal_contrib
        return risk_contrib
    
    def objective(weights, cov_matrix):
        """Minimize sum of squared deviations from equal risk contribution"""
        risk_contrib = risk_contributions(weights, cov_matrix)
        target_contrib = 1.0 / len(weights)
        return np.sum((risk_contrib - target_contrib) ** 2)
    
    # Constraints and bounds
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = [(0.001, 1) for _ in range(n_assets)]
    
    # Initial guess (equal weights)
    x0 = np.ones(n_assets) / n_assets
    
    # Optimization
    result = minimize(objective, x0, args=(cov_matrix,), 
                     method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result.x
```

### 1.3 Risk Parity Extensions

#### Hierarchical Risk Parity (HRP)
**Concept:** Use machine learning clustering to build diversified portfolios

```python
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import linkage, dendrogram

def hierarchical_risk_parity(returns):
    """
    Implement Hierarchical Risk Parity (Lopez de Prado)
    
    Parameters:
    - returns: Asset returns DataFrame
    
    Returns:
    - weights: HRP portfolio weights
    """
    
    # Step 1: Compute distance matrix
    corr_matrix = returns.corr()
    distance_matrix = np.sqrt(0.5 * (1 - corr_matrix))
    
    # Step 2: Hierarchical clustering
    linkage_matrix = linkage(distance_matrix, method='ward')
    
    # Step 3: Quasi-diagonalization
    def quasi_diag(linkage_matrix):
        """Reorganize correlation matrix based on clustering"""
        # Implementation of quasi-diagonalization algorithm
        pass
    
    # Step 4: Recursive bisection
    def recursive_bisection(cov_matrix, items):
        """Recursively allocate weights using bisection"""
        if len(items) == 1:
            return {items[0]: 1.0}
        
        # Split items into two clusters
        mid = len(items) // 2
        cluster1 = items[:mid]
        cluster2 = items[mid:]
        
        # Calculate cluster variances
        cov1 = cov_matrix.loc[cluster1, cluster1]
        cov2 = cov_matrix.loc[cluster2, cluster2]
        
        # Equal risk allocation between clusters
        var1 = np.trace(cov1) / len(cluster1)
        var2 = np.trace(cov2) / len(cluster2)
        
        alpha = var2 / (var1 + var2)
        
        # Recursive allocation within clusters
        weights1 = recursive_bisection(cov_matrix, cluster1)
        weights2 = recursive_bisection(cov_matrix, cluster2)
        
        # Combine weights
        weights = {}
        for item in cluster1:
            weights[item] = alpha * weights1[item]
        for item in cluster2:
            weights[item] = (1 - alpha) * weights2[item]
            
        return weights
    
    # Apply HRP algorithm
    cov_matrix = returns.cov()
    items = list(returns.columns)
    weights_dict = recursive_bisection(cov_matrix, items)
    
    return pd.Series(weights_dict)
```

## 2. Factor Investing Framework

### 2.1 Factor Identification and Construction
**Systematic Factors:** Market, size, value, momentum, quality, low volatility
**Factor Exposure:** Measure how much each asset loads on systematic factors
**Factor Timing:** Dynamic allocation based on factor attractiveness

### Factor Model Specification
```
R_i = α_i + β_i1 * F_1 + β_i2 * F_2 + ... + β_ik * F_k + ε_i
```

Where:
- R_i = Return of asset i
- F_j = Factor j return
- β_ij = Loading of asset i on factor j
- ε_i = Idiosyncratic return

### 2.2 Multi-Factor Portfolio Construction

```python
def multi_factor_portfolio_optimization(expected_returns, factor_loadings, 
                                      factor_covariance, idiosyncratic_var,
                                      factor_views=None, risk_aversion=1.0):
    """
    Optimize portfolio using multi-factor model
    
    Parameters:
    - expected_returns: Expected asset returns
    - factor_loadings: Asset loadings on factors (n_assets x n_factors)
    - factor_covariance: Factor covariance matrix
    - idiosyncratic_var: Asset-specific variances
    - factor_views: Optional views on factor returns
    - risk_aversion: Risk aversion parameter
    
    Returns:
    - optimal_weights: Optimal portfolio weights
    """
    
    n_assets = len(expected_returns)
    
    # Construct full covariance matrix
    factor_risk = np.dot(factor_loadings, np.dot(factor_covariance, factor_loadings.T))
    idiosyncratic_risk = np.diag(idiosyncratic_var)
    total_covariance = factor_risk + idiosyncratic_risk
    
    # Incorporate factor views if provided
    if factor_views is not None:
        # Black-Litterman style adjustment
        adjusted_returns = expected_returns + np.dot(factor_loadings, factor_views)
    else:
        adjusted_returns = expected_returns
    
    # Mean-variance optimization
    def portfolio_utility(weights):
        portfolio_return = np.dot(weights, adjusted_returns)
        portfolio_variance = np.dot(weights, np.dot(total_covariance, weights))
        return portfolio_return - 0.5 * risk_aversion * portfolio_variance
    
    # Constraints
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = [(0, 1) for _ in range(n_assets)]
    
    # Optimization
    result = minimize(lambda x: -portfolio_utility(x), 
                     x0=np.ones(n_assets) / n_assets,
                     method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result.x
```

### 2.3 Factor Timing Strategies

```python
def factor_timing_model(factor_returns, economic_indicators, lookback_window=60):
    """
    Implement factor timing based on economic indicators
    
    Parameters:
    - factor_returns: Historical factor returns
    - economic_indicators: Economic variables for prediction
    - lookback_window: Window for model estimation
    
    Returns:
    - factor_forecasts: Predicted factor returns
    """
    
    from sklearn.linear_model import LinearRegression
    
    factor_forecasts = {}
    
    for factor in factor_returns.columns:
        # Prepare data
        y = factor_returns[factor].values[lookback_window:]
        X = economic_indicators.values[:-1]  # Lag indicators by 1 period
        
        # Rolling regression
        forecasts = []
        for i in range(len(y)):
            if i < lookback_window:
                forecasts.append(0)  # No forecast for initial period
            else:
                # Fit model on rolling window
                model = LinearRegression()
                model.fit(X[i-lookback_window:i], y[i-lookback_window:i])
                
                # Forecast next period
                forecast = model.predict(X[i:i+1])[0]
                forecasts.append(forecast)
        
        factor_forecasts[factor] = forecasts
    
    return pd.DataFrame(factor_forecasts, index=factor_returns.index)
```

## 3. Smart Beta Strategies

### 3.1 Fundamental Weighting
**Concept:** Weight stocks by fundamental metrics rather than market cap

```python
def fundamental_weighted_portfolio(market_caps, fundamentals, 
                                 fundamental_weights=None):
    """
    Construct fundamentally weighted portfolio
    
    Parameters:
    - market_caps: Market capitalizations
    - fundamentals: DataFrame with fundamental metrics
    - fundamental_weights: Weights for different fundamental metrics
    
    Returns:
    - portfolio_weights: Fundamental-based weights
    """
    
    if fundamental_weights is None:
        # Equal weight to all fundamental metrics
        fundamental_weights = {col: 1.0/len(fundamentals.columns) 
                             for col in fundamentals.columns}
    
    # Calculate composite fundamental score
    composite_score = pd.Series(0, index=fundamentals.index)
    
    for metric, weight in fundamental_weights.items():
        if metric in fundamentals.columns:
            # Normalize metric (handle negative values)
            normalized_metric = fundamentals[metric].rank(pct=True)
            composite_score += weight * normalized_metric
    
    # Convert to portfolio weights
    portfolio_weights = composite_score / composite_score.sum()
    
    return portfolio_weights
```

### 3.2 Low Volatility Strategies

```python
def minimum_variance_portfolio(returns, method='sample'):
    """
    Construct minimum variance portfolio
    
    Parameters:
    - returns: Asset returns
    - method: Covariance estimation method ('sample', 'shrinkage', 'robust')
    
    Returns:
    - min_var_weights: Minimum variance portfolio weights
    """
    
    if method == 'sample':
        cov_matrix = returns.cov()
    elif method == 'shrinkage':
        # Ledoit-Wolf shrinkage estimator
        from sklearn.covariance import LedoitWolf
        lw = LedoitWolf()
        cov_matrix = pd.DataFrame(lw.fit(returns).covariance_, 
                                 index=returns.columns, columns=returns.columns)
    elif method == 'robust':
        # Robust covariance estimation
        from sklearn.covariance import MinCovDet
        mcd = MinCovDet()
        cov_matrix = pd.DataFrame(mcd.fit(returns).covariance_,
                                 index=returns.columns, columns=returns.columns)
    
    # Minimum variance optimization
    n_assets = len(returns.columns)
    
    def portfolio_variance(weights):
        return np.dot(weights, np.dot(cov_matrix, weights))
    
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = [(0, 1) for _ in range(n_assets)]
    
    result = minimize(portfolio_variance, 
                     x0=np.ones(n_assets) / n_assets,
                     method='SLSQP', bounds=bounds, constraints=constraints)
    
    return pd.Series(result.x, index=returns.columns)
```

### 3.3 Maximum Diversification Portfolio

```python
def maximum_diversification_portfolio(returns):
    """
    Construct maximum diversification portfolio (Choueifaty & Coignard)
    
    Maximizes diversification ratio: weighted average volatility / portfolio volatility
    
    Parameters:
    - returns: Asset returns
    
    Returns:
    - max_div_weights: Maximum diversification weights
    """
    
    # Calculate individual asset volatilities
    asset_vols = returns.std()
    cov_matrix = returns.cov()
    
    n_assets = len(returns.columns)
    
    def diversification_ratio(weights):
        """Calculate negative diversification ratio (for minimization)"""
        weighted_avg_vol = np.dot(weights, asset_vols)
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        return -weighted_avg_vol / portfolio_vol
    
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = [(0, 1) for _ in range(n_assets)]
    
    result = minimize(diversification_ratio,
                     x0=np.ones(n_assets) / n_assets,
                     method='SLSQP', bounds=bounds, constraints=constraints)
    
    return pd.Series(result.x, index=returns.columns)
```

## 4. Alternative Risk Premia Strategies

### 4.1 Volatility Risk Premium
**Concept:** Systematic selling of volatility to capture risk premium

```python
def volatility_risk_premium_strategy(spot_prices, implied_vols, 
                                   realized_vols, lookback=30):
    """
    Implement volatility risk premium strategy
    
    Parameters:
    - spot_prices: Underlying asset prices
    - implied_vols: Implied volatilities from options
    - realized_vols: Historical realized volatilities
    - lookback: Lookback period for realized vol calculation
    
    Returns:
    - positions: Long/short volatility positions
    """
    
    # Calculate rolling realized volatility
    returns = spot_prices.pct_change()
    realized_vol_rolling = returns.rolling(lookback).std() * np.sqrt(252)
    
    # Volatility risk premium
    vol_risk_premium = implied_vols - realized_vol_rolling
    
    # Generate signals
    # Positive premium -> sell volatility (negative position)
    # Negative premium -> buy volatility (positive position)
    positions = -np.sign(vol_risk_premium) * np.abs(vol_risk_premium)
    
    # Normalize positions
    positions = positions / positions.rolling(252).std()
    
    return positions
```

### 4.2 Carry Strategies
**Concept:** Capture return from holding higher-yielding assets

```python
def carry_strategy(asset_yields, funding_costs, fx_rates=None):
    """
    Implement carry strategy across assets
    
    Parameters:
    - asset_yields: Yields/interest rates for each asset
    - funding_costs: Cost of funding positions
    - fx_rates: Exchange rates (for currency carry)
    
    Returns:
    - carry_positions: Optimal carry positions
    """
    
    # Calculate net carry
    net_carry = asset_yields - funding_costs
    
    # Adjust for currency effects if applicable
    if fx_rates is not None:
        fx_returns = fx_rates.pct_change()
        # Adjust carry for expected FX changes (UIP deviation)
        adjusted_carry = net_carry + fx_returns.rolling(252).mean() * 252
    else:
        adjusted_carry = net_carry
    
    # Risk-adjusted carry positions
    carry_volatility = adjusted_carry.rolling(60).std()
    risk_adjusted_positions = adjusted_carry / carry_volatility
    
    # Scale positions
    positions = risk_adjusted_positions / risk_adjusted_positions.rolling(252).std()
    
    return positions
```

### 4.3 Momentum Risk Premium
**Concept:** Systematic momentum strategies across asset classes

```python
def cross_asset_momentum_strategy(asset_returns, lookback_periods=[1, 3, 6, 12]):
    """
    Implement cross-asset momentum strategy
    
    Parameters:
    - asset_returns: Returns for multiple asset classes
    - lookback_periods: Momentum calculation periods (months)
    
    Returns:
    - momentum_positions: Momentum-based positions
    """
    
    momentum_signals = pd.DataFrame(index=asset_returns.index, 
                                   columns=asset_returns.columns)
    
    for period in lookback_periods:
        # Calculate momentum for each period
        period_days = period * 21  # Approximate days per month
        momentum = asset_returns.rolling(period_days).apply(
            lambda x: (1 + x).prod() - 1
        )
        
        # Cross-sectional ranking
        momentum_rank = momentum.rank(axis=1, pct=True)
        
        # Add to combined signal
        if momentum_signals.isna().all().all():
            momentum_signals = momentum_rank / len(lookback_periods)
        else:
            momentum_signals += momentum_rank / len(lookback_periods)
    
    # Convert to positions (long top tercile, short bottom tercile)
    positions = pd.DataFrame(index=asset_returns.index, 
                           columns=asset_returns.columns)
    
    for date in momentum_signals.index:
        if not momentum_signals.loc[date].isna().any():
            signals = momentum_signals.loc[date]
            
            # Long top tercile
            positions.loc[date, signals >= 0.67] = 1
            # Short bottom tercile  
            positions.loc[date, signals <= 0.33] = -1
            # Neutral middle tercile
            positions.loc[date, (signals > 0.33) & (signals < 0.67)] = 0
    
    return positions.fillna(0)
```

## 5. Risk Budgeting and Allocation

### 5.1 Risk Budgeting Framework
**Concept:** Allocate risk budget across different sources of return

```python
def risk_budgeting_optimization(expected_returns, covariance_matrix, 
                               risk_budgets, max_weight=0.3):
    """
    Optimize portfolio subject to risk budget constraints
    
    Parameters:
    - expected_returns: Expected returns for each asset
    - covariance_matrix: Asset covariance matrix
    - risk_budgets: Target risk contribution for each asset
    - max_weight: Maximum weight constraint
    
    Returns:
    - optimal_weights: Risk budget optimal weights
    """
    
    n_assets = len(expected_returns)
    
    def risk_contributions(weights):
        """Calculate risk contributions"""
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(covariance_matrix, weights)))
        marginal_contrib = np.dot(covariance_matrix, weights) / portfolio_vol
        return weights * marginal_contrib
    
    def objective(weights):
        """Minimize tracking error to risk budgets"""
        risk_contrib = risk_contributions(weights)
        target_contrib = np.array(risk_budgets) * np.sum(risk_contrib)
        return np.sum((risk_contrib - target_contrib) ** 2)
    
    # Constraints
    constraints = [
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
        {'type': 'eq', 'fun': lambda x: np.sum(risk_budgets) - 1}  # Risk budgets sum to 1
    ]
    
    bounds = [(0.001, max_weight) for _ in range(n_assets)]
    
    result = minimize(objective, x0=np.array(risk_budgets),
                     method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result.x
```

### 5.2 Dynamic Risk Allocation

```python
def dynamic_risk_allocation(returns, economic_indicators, 
                          base_allocation, rebalance_frequency=21):
    """
    Implement dynamic risk allocation based on market conditions
    
    Parameters:
    - returns: Asset returns
    - economic_indicators: Economic state variables
    - base_allocation: Base case allocation
    - rebalance_frequency: Days between rebalancing
    
    Returns:
    - dynamic_weights: Time-varying portfolio weights
    """
    
    # Regime identification using economic indicators
    from sklearn.mixture import GaussianMixture
    
    # Fit regime model
    regime_model = GaussianMixture(n_components=3, random_state=42)
    regime_probs = regime_model.fit_predict(economic_indicators)
    
    # Define regime-specific allocations
    regime_allocations = {
        0: base_allocation * 0.8,  # Low risk regime
        1: base_allocation,        # Normal regime  
        2: base_allocation * 1.2   # High risk regime
    }
    
    # Generate dynamic weights
    dynamic_weights = pd.DataFrame(index=returns.index, 
                                  columns=returns.columns)
    
    for i, date in enumerate(returns.index[::rebalance_frequency]):
        if i < len(regime_probs):
            regime = regime_probs[i]
            weights = regime_allocations[regime]
            
            # Apply weights for rebalancing period
            end_date = min(date + pd.Timedelta(days=rebalance_frequency), 
                          returns.index[-1])
            dynamic_weights.loc[date:end_date] = weights
    
    return dynamic_weights.fillna(method='ffill')
```