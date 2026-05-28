"""
Stock Alpha Pipeline — WorldQuant Brain style factor computation & stock screening.

Usage:
    python run_pipeline.py                           # Default run (S&P 500, TOP1000)
    python run_pipeline.py --universe TOP500         # Change universe
    python run_pipeline.py --top-n 20                # Show top 20 stocks
    python run_pipeline.py --tickers AAPL MSFT GOOGL # Custom tickers
    python run_pipeline.py --start 2024-01-01 --end 2025-12-31
    python run_pipeline.py --no-cache                # Force re-download
"""

import argparse
import sys
from stock_pipeline.config import StockPipelineConfig, DEFAULT_TICKERS
from stock_pipeline.pipeline import StockPipeline
from stock_pipeline import utils


def main():
    parser = argparse.ArgumentParser(
        description="Stock Alpha Pipeline — WQ Brain style factor computation"
    )
    parser.add_argument(
        "--tickers", nargs="+", default=None,
        help="Stock tickers (default: S&P 500 liquid stocks)"
    )
    parser.add_argument(
        "--start", default="2024-01-01",
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end", default="2025-12-31",
        help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--universe", default="TOP1000",
        choices=["TOP200", "TOP500", "TOP1000", "TOP3000"],
        help="Universe size (matches WQ Brain conventions)"
    )
    parser.add_argument(
        "--top-n", type=int, default=50,
        help="Number of top stocks to report"
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Disable data caching"
    )
    parser.add_argument(
        "--output-dir", default="pipeline_output",
        help="Output directory for results"
    )

    args = parser.parse_args()

    config = StockPipelineConfig(
        tickers=args.tickers or DEFAULT_TICKERS,
        start_date=args.start,
        end_date=args.end,
        universe=args.universe,
        top_n=args.top_n,
        output_dir=args.output_dir,
        use_cache=not args.no_cache,
    )

    print(f"Stock Alpha Pipeline")
    print(f"  Tickers:   {len(config.tickers)} stocks")
    print(f"  Period:    {config.start_date} -> {config.end_date}")
    print(f"  Universe:  {config.universe} (top {config.universe_sizes[config.universe]})")
    print(f"  Top N:     {config.top_n}")
    print()

    pipeline = StockPipeline(config)
    report = pipeline.run()

    utils.print_summary(report)


if __name__ == "__main__":
    main()
