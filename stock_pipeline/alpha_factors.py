import pandas as pd
import numpy as np
from typing import Dict, List


class AlphaFactorEngine:
    def __init__(self):
        self.factor_registry: Dict[str, callable] = {}
        self._register_default_factors()

    def _register_default_factors(self):
        for name in [
            "vol_weighted_mr",  # Proven alpha: VWR mean reversion
            "mean_reversion_5",
            "mean_reversion_10",
            "momentum_5",
            "momentum_10",
            "momentum_20",
            "volume_price_5",
            "vwap_deviation",
            "vwap_deviation_normalized",
            "volatility_20",
            "volatility_reversal",
            "high_low_midpoint",
            "high_low_position",
            "liquidity_volume_ratio",
            "amihud_illiquidity",
            "volume_surge",
            "money_flow",
            "combined_mr_momentum",
        ]:
            method = getattr(self, f"factor_{name}", None)
            if method:
                self.factor_registry[name] = method

    @staticmethod
    def _rank_cross_sectional(series: pd.Series) -> pd.Series:
        ranked = series.rank(pct=True)
        return ranked.fillna(0.5)

    @staticmethod
    def _zscore_cross_sectional(series: pd.Series) -> pd.Series:
        mu = series.mean()
        sigma = series.std()
        if sigma == 0 or pd.isna(sigma):
            return pd.Series(0.0, index=series.index)
        return (series - mu) / sigma

    @staticmethod
    def _ts_delta(df: pd.DataFrame, col: str, days: int) -> pd.Series:
        return df[col] - df[col].shift(days)

    @staticmethod
    def _ts_mean(df: pd.DataFrame, col: str, days: int) -> pd.Series:
        return df[col].rolling(window=days, min_periods=days).mean()

    @staticmethod
    def _ts_std(df: pd.DataFrame, col: str, days: int) -> pd.Series:
        return df[col].rolling(window=days, min_periods=days).std()

    @staticmethod
    def _ts_covariance(df: pd.DataFrame, col1: str, col2: str, days: int) -> pd.Series:
        return df[col1].rolling(window=days, min_periods=days).cov(df[col2])

    @staticmethod
    def _ts_rank(df: pd.DataFrame, col: str, days: int) -> pd.Series:
        return df[col].rolling(window=days, min_periods=days).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False
        )

    @staticmethod
    def _ts_decay_linear(series: pd.Series, days: int) -> pd.Series:
        weights = np.arange(1, days + 1)
        weights = weights / weights.sum()

        def _decay(x):
            if len(x) < days:
                return np.nan
            return np.dot(x, weights)

        return series.rolling(window=days, min_periods=days).apply(_decay, raw=True)

    # === Alpha Factors (mirroring WQ Brain themes) ===

    def factor_mean_reversion_5(self, df: pd.DataFrame) -> pd.Series:
        delta = self._ts_delta(df, "close", 5)
        return -delta

    def factor_mean_reversion_10(self, df: pd.DataFrame) -> pd.Series:
        ret = df["close"].pct_change(periods=10)
        return -ret

    def factor_momentum_5(self, df: pd.DataFrame) -> pd.Series:
        ret = df["close"].pct_change(periods=5)
        return ret

    def factor_momentum_10(self, df: pd.DataFrame) -> pd.Series:
        ret = df["close"].pct_change(periods=10)
        return ret

    def factor_momentum_20(self, df: pd.DataFrame) -> pd.Series:
        ret = df["close"].pct_change(periods=20)
        return ret

    def factor_volume_price_5(self, df: pd.DataFrame) -> pd.Series:
        close_ranked = df["close"].rank(pct=True)
        volume_ranked = df["volume"].rank(pct=True)
        cov = close_ranked.rolling(5, min_periods=5).cov(volume_ranked)
        return -cov

    def factor_vwap_deviation(self, df: pd.DataFrame) -> pd.Series:
        approx_vwap = (df["high"] + df["low"] + df["close"]) / 3
        return approx_vwap - df["close"]

    def factor_vwap_deviation_normalized(self, df: pd.DataFrame) -> pd.Series:
        approx_vwap = (df["high"] + df["low"] + df["close"]) / 3
        returns_std = df["close"].pct_change().rolling(20, min_periods=20).std()
        deviation = (approx_vwap - df["close"]) / df["close"]
        return deviation / (returns_std + 0.001)

    def factor_volatility_20(self, df: pd.DataFrame) -> pd.Series:
        returns = df["close"].pct_change()
        vol = returns.rolling(20, min_periods=20).std()
        return -vol

    def factor_volatility_reversal(self, df: pd.DataFrame) -> pd.Series:
        returns = df["close"].pct_change()
        vol_short = returns.rolling(5, min_periods=5).std()
        vol_long = returns.rolling(20, min_periods=20).std()
        return -(vol_short / vol_long)

    def factor_high_low_midpoint(self, df: pd.DataFrame) -> pd.Series:
        midpoint = (df["high"] + df["low"]) / 2
        return midpoint - df["close"]

    def factor_high_low_position(self, df: pd.DataFrame) -> pd.Series:
        range_ = df["high"] - df["low"]
        return (df["close"] - df["low"]) / (range_ + 0.001)

    def factor_liquidity_volume_ratio(self, df: pd.DataFrame) -> pd.Series:
        adv20 = df["volume"].rolling(20, min_periods=20).mean()
        return df["volume"] / adv20

    def factor_amihud_illiquidity(self, df: pd.DataFrame) -> pd.Series:
        returns = df["close"].pct_change().abs()
        dvol = df["close"] * df["volume"]
        illiq = returns / (dvol + 1)
        return illiq.rolling(20, min_periods=20).mean()

    def factor_volume_surge(self, df: pd.DataFrame) -> pd.Series:
        volume_rank = df["volume"].rolling(20, min_periods=20).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False
        )
        return volume_rank

    def factor_money_flow(self, df: pd.DataFrame) -> pd.Series:
        direction = np.sign(df["close"] - df["open"])
        mf = direction * df["volume"]
        return mf.rolling(10, min_periods=10).sum()

    def factor_combined_mr_momentum(self, df: pd.DataFrame) -> pd.Series:
        mr = self.factor_mean_reversion_5(df)
        mom = self.factor_momentum_10(df)
        mr_ranked = mr.rank(pct=True)
        mom_ranked = mom.rank(pct=True)
        return mr_ranked * 0.5 + mom_ranked * 0.5

    # === Proven Alpha: Volume-Weighted Return Mean Reversion ===
    # Formula:
    #   lookback = 5;
    #   raw_ret  = ts_sum(returns * volume, lookback) / (ts_sum(volume, lookback) + 1);
    #   vol_std  = ts_std_dev(returns, 20);
    #   vol_signal = -rank(raw_ret / (vol_std + 0.001));

    def factor_vol_weighted_mr(self, df: pd.DataFrame) -> pd.Series:
        returns = df["close"].pct_change()
        volume = df["volume"]
        lookback = 5

        sum_ret_vol = (returns * volume).rolling(lookback, min_periods=lookback).sum()
        sum_vol = volume.rolling(lookback, min_periods=lookback).sum()
        raw_ret = sum_ret_vol / (sum_vol + 1)

        vol_std = returns.rolling(20, min_periods=20).std()
        signal = raw_ret / (vol_std + 0.001)

        ranked = signal.rank(pct=True)
        return -ranked

    def compute_factor(self, name: str, df: pd.DataFrame) -> pd.Series:
        if name not in self.factor_registry:
            raise ValueError(f"Unknown factor: {name}. Available: {list(self.factor_registry.keys())}")
        return self.factor_registry[name](df)

    def compute_all(self, df: pd.DataFrame) -> pd.DataFrame:
        result = pd.DataFrame(index=df.index)
        for name in self.factor_registry:
            try:
                series = self.compute_factor(name, df).fillna(0)
                result[name] = series
            except Exception:
                result[name] = 0.0
        return result
