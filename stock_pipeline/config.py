from dataclasses import dataclass, field
from typing import List


# S&P 500 + top liquid stocks for broad coverage
DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "JPM", "V", "JNJ", "WMT", "MA", "PG", "UNH", "HD", "DIS", "BAC",
    "KO", "PEP", "XOM", "CVX", "CSCO", "ABT", "CRM", "MCD", "NKE",
    "INTC", "VZ", "WFC", "T", "MRK", "PFE", "ABBV", "TMO", "NFLX",
    "AMD", "ADBE", "PYPL", "CMCSA", "COST", "DHR", "SLB", "BA", "GE",
    "AMGN", "IBM", "TXN", "LOW", "CAT", "RTX", "HON", "UBER", "SBUX",
    "GS", "SPGI", "BLK", "DE", "SYK", "LMT", "MDT", "NEE", "PLD",
    "SCHW", "AXP", "BKNG", "C", "MS", "ELV", "CI", "TMUS", "GILD",
    "ADP", "ISRG", "VRTX", "ETN", "REGN", "BSX", "PGR", "COP", "EOG",
    "MRNA", "F", "GM", "AAL", "UAL", "DAL", "FDX", "UPS", "MMM",
]

DEFAULT_SP500 = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "JPM", "V", "JNJ", "WMT", "MA", "PG", "UNH", "HD", "DIS", "BAC",
    "KO", "PEP", "XOM", "CVX", "CSCO", "ABT", "CRM", "MCD", "NKE",
    "INTC", "VZ", "WFC", "T", "MRK", "PFE", "ABBV", "TMO", "NFLX",
    "AMD", "ADBE", "PYPL", "CMCSA", "COST", "DHR", "BA", "GE",
    "AMGN", "IBM", "TXN", "LOW", "CAT", "HON", "UBER", "SBUX",
    "GS", "SPGI", "BLK", "DE", "SYK", "LMT", "MDT", "NEE",
    "SCHW", "AXP", "BKNG", "C", "MS", "TMUS", "GILD",
    "ADP", "ISRG", "VRTX", "ETN", "BSX", "PGR",
    "F", "GM", "FDX", "UPS", "MMM",
]


@dataclass
class StockPipelineConfig:
    tickers: List[str] = field(default_factory=lambda: DEFAULT_TICKERS)
    start_date: str = "2023-01-01"
    end_date: str = "2025-12-31"
    universe: str = "TOP1000"

    # Universe size mapping (matches WQ Brain conventions)
    universe_sizes: dict = field(default_factory=lambda: {
        "TOP200": 200,
        "TOP500": 500,
        "TOP1000": 1000,
        "TOP3000": 3000,
    })

    # Alpha factor weights for composite scoring
    # Default: chỉ dùng proven alpha vol_weighted_mr
    factor_weights: dict = field(default_factory=lambda: {
        "vol_weighted_mr": 1.0,
    })

    # Output settings
    top_n: int = 50
    output_dir: str = "pipeline_output"

    # Data cache
    cache_dir: str = "stock_data_cache"
    use_cache: bool = True
