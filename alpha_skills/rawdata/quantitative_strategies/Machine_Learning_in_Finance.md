# Machine Learning Applications in Quantitative Finance

**Focus:** Modern ML techniques for alpha generation, risk management, and portfolio optimization  
**Applications:** Systematic trading, alternative data processing, regime detection  
**Key Methods:** Deep learning, ensemble methods, reinforcement learning, NLP

## Overview

Machine learning has revolutionized quantitative finance by enabling the processing of vast amounts of data, 
discovering complex patterns, and adapting to changing market conditions. This document covers practical 
applications of ML in finance with implementation examples and best practices.

## 1. Supervised Learning for Return Prediction

### 1.1 Feature Engineering for Financial Data
**Concept:** Transform raw market data into predictive features

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from ta import add_all_ta_features

def create_financial_features(price_data, volume_data, fundamental_data=None):
    """
    Create comprehensive feature set for ML models
    
    Parameters:
    - price_data: OHLC price data
    - volume_data: Trading volume data
    - fundamental_data: Optional fundamental data
    
    Returns:
    - features: Engineered feature matrix
    """
    
    features = pd.DataFrame(index=price_data.index)
    
    # Price-based features
    features['returns_1d'] = price_data['close'].pct_change()
    features['returns_5d'] = price_data['close'].pct_change(5)
    features['returns_20d'] = price_data['close'].pct_change(20)
    
    # Volatility features
    features['volatility_5d'] = features['returns_1d'].rolling(5).std()
    features['volatility_20d'] = features['returns_1d'].rolling(20).std()
    features['volatility_ratio'] = features['volatility_5d'] / features['volatility_20d']
    
    # Technical indicators
    price_data_ta = add_all_ta_features(price_data, 
                                       open="open", high="high", 
                                       low="low", close="close", 
                                       volume="volume")
    
    # Select key technical indicators
    ta_features = [col for col in price_data_ta.columns if col.startswith(('trend_', 'momentum_', 'volatility_'))]
    features = pd.concat([features, price_data_ta[ta_features]], axis=1)
    
    # Volume features
    features['volume_sma_ratio'] = volume_data / volume_data.rolling(20).mean()
    features['volume_momentum'] = volume_data.pct_change(5)
    
    # Cross-sectional features (if multiple assets)
    if isinstance(price_data, pd.DataFrame) and len(price_data.columns) > 4:
        # Relative performance
        market_return = price_data['close'].pct_change().mean(axis=1)
        features['relative_performance'] = features['returns_1d'] - market_return
        
        # Relative volatility
        market_vol = price_data['close'].pct_change().std(axis=1)
        features['relative_volatility'] = features['volatility_20d'] / market_vol
    
    # Fundamental features (if available)
    if fundamental_data is not None:
        features['pe_ratio'] = fundamental_data['price'] / fundamental_data['earnings_per_share']
        features['pb_ratio'] = fundamental_data['price'] / fundamental_data['book_value_per_share']
        features['debt_to_equity'] = fundamental_data['total_debt'] / fundamental_data['total_equity']
    
    return features.dropna()
```

### 1.2 Ensemble Methods for Alpha Generation
**Concept:** Combine multiple models to improve prediction accuracy

```python
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.svm import SVR
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb

class AlphaEnsemble:
    """
    Ensemble model for alpha generation
    """
    
    def __init__(self, models=None, meta_model=None):
        if models is None:
            self.models = {
                'rf': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
                'gbm': GradientBoostingRegressor(n_estimators=100, max_depth=6, random_state=42),
                'xgb': xgb.XGBRegressor(n_estimators=100, max_depth=6, random_state=42),
                'linear': Ridge(alpha=1.0),
                'svm': SVR(kernel='rbf', C=1.0)
            }
        else:
            self.models = models
            
        self.meta_model = meta_model or LinearRegression()
        self.is_fitted = False
        
    def fit(self, X, y, validation_split=0.2):
        """
        Fit ensemble model with cross-validation
        """
        
        # Time series split for validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # First level predictions
        meta_features = np.zeros((len(X), len(self.models)))
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            for i, (name, model) in enumerate(self.models.items()):
                # Fit model on training data
                model.fit(X_train, y_train)
                
                # Predict on validation data
                val_pred = model.predict(X_val)
                meta_features[val_idx, i] = val_pred
        
        # Fit meta-model
        self.meta_model.fit(meta_features, y)
        
        # Fit base models on full data
        for model in self.models.values():
            model.fit(X, y)
            
        self.is_fitted = True
        
    def predict(self, X):
        """
        Generate ensemble predictions
        """
        
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        # Get base model predictions
        base_predictions = np.zeros((len(X), len(self.models)))
        
        for i, model in enumerate(self.models.values()):
            base_predictions[:, i] = model.predict(X)
        
        # Meta-model prediction
        ensemble_prediction = self.meta_model.predict(base_predictions)
        
        return ensemble_prediction
    
    def feature_importance(self):
        """
        Get feature importance from tree-based models
        """
        
        importance_dict = {}
        
        for name, model in self.models.items():
            if hasattr(model, 'feature_importances_'):
                importance_dict[name] = model.feature_importances_
        
        return importance_dict
```