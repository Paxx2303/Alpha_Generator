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
### 1.3 Deep Learning for Sequential Data
**Concept:** Use neural networks to capture temporal dependencies

```python
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class FinancialTimeSeriesDataset(Dataset):
    """
    Dataset class for financial time series
    """
    
    def __init__(self, features, targets, sequence_length=60):
        self.features = features
        self.targets = targets
        self.sequence_length = sequence_length
        
    def __len__(self):
        return len(self.features) - self.sequence_length
    
    def __getitem__(self, idx):
        X = self.features[idx:idx + self.sequence_length]
        y = self.targets[idx + self.sequence_length]
        
        return torch.FloatTensor(X), torch.FloatTensor([y])

class LSTMAlphaModel(nn.Module):
    """
    LSTM model for alpha prediction
    """
    
    def __init__(self, input_size, hidden_size=128, num_layers=2, dropout=0.2):
        super(LSTMAlphaModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=dropout)
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(hidden_size, num_heads=8)
        
        # Output layers
        self.fc1 = nn.Linear(hidden_size, 64)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, 32)
        self.output = nn.Linear(32, 1)
        
        # Activation functions
        self.relu = nn.ReLU()
        self.tanh = nn.Tanh()
        
    def forward(self, x):
        # LSTM forward pass
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Apply attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Use last time step
        last_output = attn_out[:, -1, :]
        
        # Fully connected layers
        out = self.relu(self.fc1(last_output))
        out = self.dropout(out)
        out = self.relu(self.fc2(out))
        out = self.tanh(self.output(out))  # Bounded output
        
        return out

def train_lstm_model(features, targets, epochs=100, batch_size=32, learning_rate=0.001):
    """
    Train LSTM model for alpha prediction
    """
    
    # Create dataset and dataloader
    dataset = FinancialTimeSeriesDataset(features.values, targets.values)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    # Initialize model
    input_size = features.shape[1]
    model = LSTMAlphaModel(input_size)
    
    # Loss function and optimizer
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10)
    
    # Training loop
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        
        for batch_X, batch_y in dataloader:
            optimizer.zero_grad()
            
            # Forward pass
            predictions = model(batch_X)
            loss = criterion(predictions, batch_y)
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        scheduler.step(avg_loss)
        
        if epoch % 10 == 0:
            print(f'Epoch {epoch}, Loss: {avg_loss:.6f}')
    
    return model
```

## 2. Unsupervised Learning for Market Regime Detection

### 2.1 Clustering for Market Regimes
**Concept:** Identify different market states using clustering algorithms

```python
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

class MarketRegimeDetector:
    """
    Detect market regimes using unsupervised learning
    """
    
    def __init__(self, method='gmm', n_regimes=3):
        self.method = method
        self.n_regimes = n_regimes
        self.model = None
        self.scaler = StandardScaler()
        
    def prepare_regime_features(self, returns, volume=None, volatility_window=20):
        """
        Prepare features for regime detection
        """
        
        features = pd.DataFrame(index=returns.index)
        
        # Return-based features
        features['return_mean'] = returns.rolling(volatility_window).mean()
        features['return_std'] = returns.rolling(volatility_window).std()
        features['return_skew'] = returns.rolling(volatility_window).skew()
        features['return_kurt'] = returns.rolling(volatility_window).kurt()
        
        # Volatility clustering
        features['volatility'] = returns.rolling(volatility_window).std()
        features['volatility_change'] = features['volatility'].pct_change()
        
        # Trend features
        features['trend_5d'] = returns.rolling(5).mean()
        features['trend_20d'] = returns.rolling(20).mean()
        features['trend_ratio'] = features['trend_5d'] / features['trend_20d']
        
        # Volume features (if available)
        if volume is not None:
            features['volume_trend'] = volume.rolling(20).mean()
            features['volume_volatility'] = volume.rolling(20).std()
        
        return features.dropna()
    
    def fit(self, features):
        """
        Fit regime detection model
        """
        
        # Standardize features
        features_scaled = self.scaler.fit_transform(features)
        
        if self.method == 'kmeans':
            self.model = KMeans(n_clusters=self.n_regimes, random_state=42)
        elif self.method == 'gmm':
            self.model = GaussianMixture(n_components=self.n_regimes, random_state=42)
        elif self.method == 'dbscan':
            self.model = DBSCAN(eps=0.5, min_samples=5)
        
        # Fit model
        if self.method in ['kmeans', 'dbscan']:
            regime_labels = self.model.fit_predict(features_scaled)
        else:  # GMM
            self.model.fit(features_scaled)
            regime_labels = self.model.predict(features_scaled)
        
        return regime_labels
    
    def predict_regime_probabilities(self, features):
        """
        Predict regime probabilities (for GMM)
        """
        
        if self.method != 'gmm':
            raise ValueError("Regime probabilities only available for GMM")
        
        features_scaled = self.scaler.transform(features)
        return self.model.predict_proba(features_scaled)
    
    def visualize_regimes(self, features, regime_labels):
        """
        Visualize detected regimes using PCA
        """
        
        # Apply PCA for visualization
        pca = PCA(n_components=2)
        features_pca = pca.fit_transform(self.scaler.transform(features))
        
        # Plot regimes
        plt.figure(figsize=(10, 8))
        scatter = plt.scatter(features_pca[:, 0], features_pca[:, 1], 
                            c=regime_labels, cmap='viridis', alpha=0.6)
        plt.colorbar(scatter)
        plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
        plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
        plt.title('Market Regimes in PCA Space')
        plt.show()
        
        return pca
```

### 2.2 Hidden Markov Models for Regime Switching
**Concept:** Model regime transitions as hidden Markov process

```python
from hmmlearn import hmm
import numpy as np

class HiddenMarkovRegimeModel:
    """
    Hidden Markov Model for regime detection
    """
    
    def __init__(self, n_regimes=3, covariance_type='full'):
        self.n_regimes = n_regimes
        self.covariance_type = covariance_type
        self.model = None
        
    def fit(self, returns, n_iter=100):
        """
        Fit HMM to return data
        """
        
        # Prepare data (returns and volatility)
        volatility = returns.rolling(20).std()
        data = np.column_stack([returns.values, volatility.values])
        data = data[~np.isnan(data).any(axis=1)]  # Remove NaN values
        
        # Initialize HMM
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type=self.covariance_type,
            n_iter=n_iter,
            random_state=42
        )
        
        # Fit model
        self.model.fit(data)
        
        # Get regime sequence
        regime_sequence = self.model.predict(data)
        
        return regime_sequence
    
    def predict_regimes(self, returns):
        """
        Predict regimes for new data
        """
        
        volatility = returns.rolling(20).std()
        data = np.column_stack([returns.values, volatility.values])
        data = data[~np.isnan(data).any(axis=1)]
        
        return self.model.predict(data)
    
    def get_regime_probabilities(self, returns):
        """
        Get regime probabilities
        """
        
        volatility = returns.rolling(20).std()
        data = np.column_stack([returns.values, volatility.values])
        data = data[~np.isnan(data).any(axis=1)]
        
        return self.model.predict_proba(data)
    
    def analyze_regimes(self, returns, regime_sequence):
        """
        Analyze characteristics of each regime
        """
        
        regime_stats = {}
        
        for regime in range(self.n_regimes):
            regime_mask = regime_sequence == regime
            regime_returns = returns[regime_mask]
            
            regime_stats[regime] = {
                'mean_return': regime_returns.mean(),
                'volatility': regime_returns.std(),
                'skewness': regime_returns.skew(),
                'kurtosis': regime_returns.kurtosis(),
                'frequency': regime_mask.sum() / len(regime_sequence),
                'avg_duration': self._calculate_avg_duration(regime_mask)
            }
        
        return regime_stats
    
    def _calculate_avg_duration(self, regime_mask):
        """
        Calculate average duration of regime
        """
        
        durations = []
        current_duration = 0
        
        for is_regime in regime_mask:
            if is_regime:
                current_duration += 1
            else:
                if current_duration > 0:
                    durations.append(current_duration)
                    current_duration = 0
        
        if current_duration > 0:
            durations.append(current_duration)
        
        return np.mean(durations) if durations else 0
```

## 3. Reinforcement Learning for Portfolio Management

### 3.1 Deep Q-Network for Trading
**Concept:** Learn optimal trading actions through trial and error

```python
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque

class TradingEnvironment:
    """
    Trading environment for reinforcement learning
    """
    
    def __init__(self, price_data, initial_balance=10000, transaction_cost=0.001):
        self.price_data = price_data
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost
        self.reset()
        
    def reset(self):
        """
        Reset environment to initial state
        """
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0  # Number of shares held
        self.total_value = self.initial_balance
        
        return self._get_state()
    
    def _get_state(self):
        """
        Get current state representation
        """
        if self.current_step >= len(self.price_data) - 1:
            return None
        
        # Price features
        current_price = self.price_data.iloc[self.current_step]['close']
        price_history = self.price_data.iloc[max(0, self.current_step-20):self.current_step+1]['close'].values
        
        # Normalize price history
        if len(price_history) > 1:
            price_returns = np.diff(price_history) / price_history[:-1]
            price_features = np.pad(price_returns, (20-len(price_returns), 0), 'constant')
        else:
            price_features = np.zeros(20)
        
        # Portfolio features
        portfolio_value = self.balance + self.position * current_price
        portfolio_features = [
            self.balance / self.initial_balance,  # Normalized cash
            self.position * current_price / self.initial_balance,  # Normalized position value
            portfolio_value / self.initial_balance  # Normalized total value
        ]
        
        state = np.concatenate([price_features, portfolio_features])
        return state
    
    def step(self, action):
        """
        Execute action and return new state, reward, done
        
        Actions: 0=Hold, 1=Buy, 2=Sell
        """
        if self.current_step >= len(self.price_data) - 1:
            return None, 0, True
        
        current_price = self.price_data.iloc[self.current_step]['close']
        next_price = self.price_data.iloc[self.current_step + 1]['close']
        
        # Execute action
        if action == 1:  # Buy
            max_shares = int(self.balance / (current_price * (1 + self.transaction_cost)))
            if max_shares > 0:
                shares_to_buy = max_shares
                cost = shares_to_buy * current_price * (1 + self.transaction_cost)
                self.balance -= cost
                self.position += shares_to_buy
        
        elif action == 2:  # Sell
            if self.position > 0:
                proceeds = self.position * current_price * (1 - self.transaction_cost)
                self.balance += proceeds
                self.position = 0
        
        # Move to next step
        self.current_step += 1
        
        # Calculate reward (change in portfolio value)
        new_portfolio_value = self.balance + self.position * next_price
        reward = (new_portfolio_value - self.total_value) / self.total_value
        self.total_value = new_portfolio_value
        
        # Get next state
        next_state = self._get_state()
        done = self.current_step >= len(self.price_data) - 1
        
        return next_state, reward, done

class DQNAgent:
    """
    Deep Q-Network agent for trading
    """
    
    def __init__(self, state_size, action_size, learning_rate=0.001):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000)
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = learning_rate
        
        # Neural networks
        self.q_network = self._build_model()
        self.target_network = self._build_model()
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
    def _build_model(self):
        """
        Build neural network for Q-function approximation
        """
        model = nn.Sequential(
            nn.Linear(self.state_size, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, self.action_size)
        )
        return model
    
    def remember(self, state, action, reward, next_state, done):
        """
        Store experience in replay buffer
        """
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        """
        Choose action using epsilon-greedy policy
        """
        if np.random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.q_network(state_tensor)
        return np.argmax(q_values.cpu().data.numpy())
    
    def replay(self, batch_size=32):
        """
        Train the model on a batch of experiences
        """
        if len(self.memory) < batch_size:
            return
        
        batch = random.sample(self.memory, batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch])
        rewards = torch.FloatTensor([e[2] for e in batch])
        next_states = torch.FloatTensor([e[3] for e in batch if e[3] is not None])
        dones = torch.BoolTensor([e[4] for e in batch])
        
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        next_q_values = torch.zeros(batch_size)
        if len(next_states) > 0:
            next_q_values[~dones] = self.target_network(next_states).max(1)[0].detach()
        
        target_q_values = rewards + (0.95 * next_q_values)
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def update_target_network(self):
        """
        Update target network weights
        """
        self.target_network.load_state_dict(self.q_network.state_dict())
```