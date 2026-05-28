import os
import json
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Optional


class DataFetcher:
    def __init__(self, cache_dir: str = "stock_data_cache", use_cache: bool = True):
        self.cache_dir = cache_dir
        self.use_cache = use_cache
        if use_cache:
            os.makedirs(cache_dir, exist_ok=True)

    def fetch_ticker(self, ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
        cache_path = os.path.join(self.cache_dir, f"{ticker}.parquet")
        if self.use_cache and os.path.exists(cache_path):
            try:
                df = pd.read_parquet(cache_path)
                if not df.empty:
                    return df
            except Exception:
                pass

        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start, end=end, auto_adjust=True)
            if df.empty:
                return None
            df.index = pd.to_datetime(df.index)
            df.index.name = "date"
            df.columns = [c.lower() for c in df.columns]
            df["ticker"] = ticker

            if self.use_cache:
                df.to_parquet(cache_path)
            return df
        except Exception:
            return None

    def fetch_batch(
        self, tickers: List[str], start: str, end: str, max_workers: int = 10
    ) -> pd.DataFrame:
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.fetch_ticker, t, start, end): t
                for t in tickers
            }
            for future in as_completed(futures):
                t = futures[future]
                try:
                    df = future.result()
                    if df is not None and not df.empty:
                        results[t] = df
                except Exception:
                    continue

        if not results:
            return pd.DataFrame()

        combined = pd.concat(results.values())
        combined = combined.reset_index().set_index(["date", "ticker"])
        return combined

    def get_available_tickers(self, tickers: List[str], start: str, end: str) -> List[str]:
        available = []
        for t in tickers:
            df = self.fetch_ticker(t, start, end)
            if df is not None and not df.empty:
                available.append(t)
        return available
