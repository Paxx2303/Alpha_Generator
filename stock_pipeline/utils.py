import json
import os
import pandas as pd
from typing import Dict, List


def save_results(results: Dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "pipeline_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)


def save_top_stocks_csv(
    factor_df: pd.DataFrame,
    screener: "StockScreener",
    dates: List[pd.Timestamp],
    output_dir: str,
):
    os.makedirs(output_dir, exist_ok=True)
    all_rows = []
    for date in dates:
        top = screener.get_top_stocks(factor_df, date, top_n=50)
        if top.empty:
            continue
        for idx, row in top.iterrows():
            ticker = idx[1] if isinstance(idx, tuple) else idx
            all_rows.append({
                "date": str(date.date()),
                "ticker": ticker,
                "rank": int(row.get("rank", 0)),
                "composite_score": round(float(row.get("composite_score", 0)), 4),
                "percentile": round(float(row.get("percentile", 0)), 4),
                "signal": row.get("signal", ""),
            })

    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_csv(os.path.join(output_dir, "top_stocks_daily.csv"), index=False)


def print_summary(report: Dict):
    print("=" * 60)
    print("STOCK PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Universe: {report['config']['universe']}")
    print(f"Top N: {report['config']['top_n']}")
    print(f"Factor Weights: {report['config']['factor_weights']}")
    print("-" * 60)
    print("Daily Top Picks:")
    for day in report.get("daily_summary", [])[:5]:
        print(f"  {day['date']}: {', '.join(day['top_tickers'][:5])} "
              f"(analyzed {day['num_stocks_analyzed']} stocks)")
    print("-" * 60)
    print("Factor Statistics:")
    for factor, stats in report.get("factor_performance", {}).items():
        print(f"  {factor}: mean={stats['mean']:.4f}, std={stats['std']:.4f}")
    print("=" * 60)
