import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

from .config import StockPipelineConfig
from .data_fetcher import DataFetcher
from .alpha_factors import AlphaFactorEngine
from .stock_screener import StockScreener
from . import utils


class StockPipeline:
    def __init__(self, config: Optional[StockPipelineConfig] = None):
        self.config = config or StockPipelineConfig()
        self.fetcher = DataFetcher(
            cache_dir=self.config.cache_dir,
            use_cache=self.config.use_cache,
        )
        self.factor_engine = AlphaFactorEngine()
        self.screener = StockScreener(self.config)

        self.raw_data: pd.DataFrame = pd.DataFrame()
        self.factor_data: pd.DataFrame = pd.DataFrame()

    def fetch_data(self) -> pd.DataFrame:
        print(f"[Pipeline] Fetching data for {len(self.config.tickers)} tickers...")
        print(f"  Period: {self.config.start_date} -> {self.config.end_date}")
        self.raw_data = self.fetcher.fetch_batch(
            self.config.tickers,
            self.config.start_date,
            self.config.end_date,
        )
        print(f"  Retrieved {len(self.raw_data)} rows across "
              f"{self.raw_data.index.get_level_values('ticker').nunique()} tickers")
        return self.raw_data

    def compute_factors(self) -> pd.DataFrame:
        if self.raw_data.empty:
            raise ValueError("No data. Run fetch_data() first.")

        print("[Pipeline] Computing alpha factors...")
        tickers = self.raw_data.index.get_level_values("ticker").unique()
        all_factors = []

        for ticker in tickers:
            df_t = self.raw_data.xs(ticker, level="ticker").copy()
            df_t = df_t.sort_index()

            factors = self.factor_engine.compute_all(df_t)
            factors["ticker"] = ticker
            factors = factors.reset_index().set_index(["date", "ticker"])
            all_factors.append(factors)

        self.factor_data = pd.concat(all_factors).sort_index()
        n_dates = self.factor_data.index.get_level_values("date").nunique()
        print(f"  Computed {len(self.factor_engine.factor_registry)} factors "
              f"across {n_dates} trading days")
        return self.factor_data

    def run(self, fetch: bool = True) -> Dict:
        if fetch:
            self.fetch_data()
        if self.factor_data.empty and not self.raw_data.empty:
            self.compute_factors()
        elif self.factor_data.empty:
            self.fetch_data()
            self.compute_factors()

        print("[Pipeline] Screening and ranking stocks...")
        dates = sorted(self.factor_data.index.get_level_values("date").unique())
        latest_dates = dates[-min(10, len(dates)):]

        report = self.screener.generate_report(self.factor_data, dates=latest_dates)
        report["pipeline_info"] = {
            "run_timestamp": str(datetime.now()),
            "tickers_analyzed": len(self.config.tickers),
            "date_range": f"{self.config.start_date} → {self.config.end_date}",
            "trading_days": len(dates),
            "factors_used": list(self.factor_engine.factor_registry.keys()),
        }

        utils.save_results(report, self.config.output_dir)
        utils.save_top_stocks_csv(
            self.factor_data, self.screener, latest_dates, self.config.output_dir
        )

        print(f"[Pipeline] Results saved to '{self.config.output_dir}/'")
        return report
