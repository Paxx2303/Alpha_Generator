"""
analytics/market_data.py — External market data crawler.

Fetches real OHLCV data from Yahoo Finance (yfinance) for a basket of
S&P 500 / liquid US stocks. Used as Step 1 input for real signal analysis
before wasting WQB simulation quota.

Stores data in data/market_cache.db (SQLite) for offline reuse.
Cache TTL: 24 hours — re-crawls if stale.
"""
from __future__ import annotations

import sqlite3
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent

# Default ticker basket: ~200 liquid US stocks across all sectors
# Expanded for stable IC estimates (more cross-section = lower IC variance)
DEFAULT_TICKERS = [
    # ── Tech (30) ────────────────────────────────────────────────────────────
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA", "AMD", "INTC", "CRM",
    "ORCL", "CSCO", "ADBE", "QCOM", "TXN", "AVGO", "MU", "AMAT", "LRCX", "KLAC",
    "NOW", "SNOW", "PANW", "CRWD", "NET", "DDOG", "ZS", "FTNT", "PLTR", "UBER",
    # ── Finance (25) ──────────────────────────────────────────────────────────
    "JPM", "BAC", "GS", "WFC", "MS", "BLK", "C", "AXP", "V", "MA",
    "COF", "USB", "PNC", "TFC", "SCHW", "ICE", "CME", "SPGI", "MCO", "AON",
    "MMC", "CB", "MET", "PRU", "AFL",
    # ── Healthcare (25) ───────────────────────────────────────────────────────
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "BMY", "LLY", "CVS", "ABT", "MDT",
    "TMO", "DHR", "BSX", "SYK", "EW", "ISRG", "REGN", "VRTX", "GILD", "AMGN",
    "HUM", "CI", "ELV", "CNC", "MOH",
    # ── Energy (20) ───────────────────────────────────────────────────────────
    "XOM", "CVX", "COP", "SLB", "EOG", "PSX", "MPC", "VLO", "OXY", "HAL",
    "PXD", "DVN", "HES", "MRO", "APA", "FANG", "BKR", "NOV", "KMI", "WMB",
    # ── Consumer Discretionary (20) ───────────────────────────────────────────
    "AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "TGT", "DIS", "NFLX", "LOW",
    "F", "GM", "TJX", "ROST", "BKNG", "MAR", "HLT", "YUM", "CMG", "DHI",
    # ── Consumer Staples (15) ─────────────────────────────────────────────────
    "WMT", "COST", "PG", "KO", "PEP", "PM", "MO", "MDLZ", "GIS", "K",
    "CL", "CHD", "SJM", "CAG", "HRL",
    # ── Industrials (20) ──────────────────────────────────────────────────────
    "BA", "CAT", "GE", "MMM", "HON", "UPS", "FDX", "LMT", "RTX", "DE",
    "NOC", "GD", "ETN", "EMR", "PH", "ROK", "ITW", "DOV", "XYL", "CARR",
    # ── Materials (10) ────────────────────────────────────────────────────────
    "LIN", "APD", "NEM", "FCX", "NUE", "STLD", "VMC", "MLM", "ALB", "CF",
    # ── Utilities (10) ────────────────────────────────────────────────────────
    "NEE", "DUK", "SO", "D", "AEP", "SRE", "XEL", "ES", "WEC", "EXC",
    # ── Real Estate (10) ──────────────────────────────────────────────────────
    "AMT", "PLD", "SPG", "EQR", "AVB", "EQIX", "DLR", "PSA", "O", "WELL",
    # ── Communication (10) ────────────────────────────────────────────────────
    "GOOGL", "META", "NFLX", "DIS", "CMCSA", "VZ", "T", "TMUS", "CHTR", "DISH",
]
# De-duplicate while preserving order
DEFAULT_TICKERS = list(dict.fromkeys(DEFAULT_TICKERS))


class MarketDataCrawler:
    """
    Fetches OHLCV + basic derived features from Yahoo Finance.

    Returns a dict keyed by ticker:
        {
          "AAPL": {
            "dates": [...],
            "close": [...],
            "open":  [...],
            "high":  [...],
            "low":   [...],
            "volume":[...],
            "returns":[...],  # daily pct return
          },
          ...
        }

    Parameters
    ----------
    tickers   : list of ticker symbols (default: DEFAULT_TICKERS)
    lookback  : calendar days of history to fetch (default: 365 = 1 year)
    cache_db  : path to SQLite cache file
    cache_ttl : cache lifetime in hours (default: 24)
    """

    def __init__(
        self,
        tickers: Optional[list[str]] = None,
        lookback: int = 365,
        cache_db: Optional[Path] = None,
        cache_ttl: int = 24,
    ):
        self.tickers = tickers or DEFAULT_TICKERS
        self.lookback = lookback
        self.cache_db = cache_db or ROOT / "data" / "market_cache.db"
        self.cache_ttl = cache_ttl
        self._init_cache()

    def _init_cache(self):
        self.cache_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.cache_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                ticker   TEXT NOT NULL,
                crawled_at TEXT NOT NULL,
                data     TEXT NOT NULL,
                PRIMARY KEY (ticker)
            )
        """)
        conn.commit()
        conn.close()

    def run(self) -> dict[str, dict]:
        """Fetch all tickers. Returns per-ticker OHLCV dict."""
        result: dict[str, dict] = {}
        stale: list[str] = []

        # Check cache
        conn = sqlite3.connect(self.cache_db)
        for ticker in self.tickers:
            row = conn.execute(
                "SELECT crawled_at, data FROM market_data WHERE ticker=?", (ticker,)
            ).fetchone()
            if row:
                crawled_at = datetime.fromisoformat(row[0])
                age_hours = (datetime.now() - crawled_at).total_seconds() / 3600
                if age_hours < self.cache_ttl:
                    result[ticker] = json.loads(row[1])
                    continue
            stale.append(ticker)
        conn.close()

        if stale:
            print(f"  [market_data] Fetching {len(stale)} tickers from Yahoo Finance...")
            fetched = self._fetch_yfinance(stale)
            if fetched:
                self._save_cache(fetched)
                result.update(fetched)
        else:
            print(f"  [market_data] All {len(self.tickers)} tickers loaded from cache.")

        valid = {k: v for k, v in result.items() if v and v.get("close")}
        print(f"  [market_data] {len(valid)} tickers with valid data.")
        return valid

    def _fetch_yfinance(self, tickers: list[str]) -> dict[str, dict]:
        try:
            import yfinance as yf
        except ImportError:
            print("  [market_data] yfinance not installed — run: pip install yfinance")
            return {}

        end = datetime.now()
        start = end - timedelta(days=self.lookback)
        result: dict[str, dict] = {}

        # Batch download all at once (faster)
        try:
            raw = yf.download(
                tickers=" ".join(tickers),
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as e:
            print(f"  [market_data] yfinance batch error: {e}")
            return {}

        if raw.empty:
            return {}

        # Flatten multi-level columns
        if isinstance(raw.columns, type(raw.columns)) and hasattr(raw.columns, "levels"):
            # Multi-ticker response has (field, ticker) column tuples
            for ticker in tickers:
                try:
                    df = raw.xs(ticker, axis=1, level=1).dropna()
                    if df.empty:
                        continue
                    closes = df["Close"].tolist()
                    returns = [0.0] + [
                        (closes[i] - closes[i - 1]) / closes[i - 1]
                        if closes[i - 1] != 0 else 0.0
                        for i in range(1, len(closes))
                    ]
                    result[ticker] = {
                        "dates":   [str(d)[:10] for d in df.index.tolist()],
                        "close":   closes,
                        "open":    df["Open"].tolist(),
                        "high":    df["High"].tolist(),
                        "low":     df["Low"].tolist(),
                        "volume":  df["Volume"].tolist(),
                        "returns": returns,
                    }
                except Exception:
                    continue
        else:
            # Single ticker
            if len(tickers) == 1:
                ticker = tickers[0]
                df = raw.dropna()
                closes = df["Close"].tolist()
                returns = [0.0] + [
                    (closes[i] - closes[i - 1]) / closes[i - 1]
                    if closes[i - 1] != 0 else 0.0
                    for i in range(1, len(closes))
                ]
                result[ticker] = {
                    "dates":   [str(d)[:10] for d in df.index.tolist()],
                    "close":   closes,
                    "open":    df["Open"].tolist(),
                    "high":    df["High"].tolist(),
                    "low":     df["Low"].tolist(),
                    "volume":  df["Volume"].tolist(),
                    "returns": returns,
                }

        return result

    def _save_cache(self, data: dict[str, dict]):
        conn = sqlite3.connect(self.cache_db)
        now = datetime.now().isoformat()
        for ticker, d in data.items():
            conn.execute(
                "INSERT OR REPLACE INTO market_data (ticker, crawled_at, data) VALUES (?,?,?)",
                (ticker, now, json.dumps(d)),
            )
        conn.commit()
        conn.close()
