import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class StockScreener:
    def __init__(self, config):
        self.config = config
        self.universe_sizes = config.universe_sizes
        self.factor_weights = config.factor_weights

    def filter_universe(
        self,
        factor_df: pd.DataFrame,
        date: pd.Timestamp,
        universe: str = "TOP1000",
        liquidity_col: str = "liquidity_volume_ratio",
    ) -> pd.DataFrame:
        n = self.universe_sizes.get(universe, 1000)

        if date not in factor_df.index.get_level_values("date"):
            return pd.DataFrame()

        df_date = factor_df.xs(date, level="date", drop_level=False).copy()

        if liquidity_col in df_date.columns:
            df_date = df_date.sort_values(liquidity_col, ascending=False)
            df_date = df_date.head(min(n, len(df_date)))

        df_date = df_date.dropna(how="all")
        return df_date

    def compute_composite_score(
        self, factor_df: pd.DataFrame, weights: Optional[Dict[str, float]] = None
    ) -> pd.Series:
        if weights is None:
            weights = self.factor_weights

        score = pd.Series(0.0, index=factor_df.index)
        total_weight = 0.0

        for factor_name, weight in weights.items():
            if factor_name in factor_df.columns:
                ranked = factor_df[factor_name].rank(pct=True).fillna(0.5)
                score += weight * ranked
                total_weight += weight

        if total_weight > 0:
            score = score / total_weight

        return score

    def rank_stocks(
        self, factor_df: pd.DataFrame, date: pd.Timestamp
    ) -> pd.DataFrame:
        df_date = self.filter_universe(factor_df, date, universe=self.config.universe)
        if df_date.empty:
            return pd.DataFrame()

        df_date["composite_score"] = self.compute_composite_score(df_date)

        df_date["rank"] = df_date["composite_score"].rank(ascending=False)
        df_date["percentile"] = df_date["composite_score"].rank(pct=True)

        df_date = df_date.sort_values("rank")
        df_date["signal"] = "BUY"
        df_date.loc[df_date["percentile"] < 0.3, "signal"] = "NEUTRAL"
        df_date.loc[df_date["percentile"] < 0.1, "signal"] = "SELL"

        return df_date

    def get_top_stocks(
        self, factor_df: pd.DataFrame, date: pd.Timestamp, top_n: Optional[int] = None
    ) -> pd.DataFrame:
        if top_n is None:
            top_n = self.config.top_n

        ranked = self.rank_stocks(factor_df, date)
        if ranked.empty:
            return ranked

        return ranked.head(top_n)

    def generate_report(
        self, factor_df: pd.DataFrame, dates: Optional[List[pd.Timestamp]] = None
    ) -> Dict:
        all_dates = sorted(factor_df.index.get_level_values("date").unique())
        if dates is None:
            dates = all_dates

        report = {
            "config": {
                "universe": self.config.universe,
                "factor_weights": self.factor_weights,
                "top_n": self.config.top_n,
            },
            "daily_summary": [],
            "factor_performance": {},
        }

        for date in dates:
            ranked = self.rank_stocks(factor_df, date)
            if ranked.empty:
                continue

            top = ranked.head(min(self.config.top_n, len(ranked)))
            tickers = [idx[1] if isinstance(idx, tuple) else idx for idx in top.index]

            daily = {
                "date": str(date.date()),
                "top_tickers": tickers[:10],
                "num_stocks_analyzed": len(ranked),
                "avg_composite_score": float(ranked["composite_score"].mean()),
                "top_score": float(ranked["composite_score"].max()),
            }
            report["daily_summary"].append(daily)

        for factor in factor_df.columns:
            if factor in self.factor_weights:
                vals = factor_df[factor].replace([np.inf, -np.inf], np.nan)
                valid = vals.dropna()
                report["factor_performance"][factor] = {
                    "mean": float(valid.mean()),
                    "std": float(valid.std()),
                    "weight": self.factor_weights.get(factor, 1.0),
                }

        return report
