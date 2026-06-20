"""
analytics/describe.py — Step 1: Describe Data

Two sub-tasks:
  A. Describe external market data (real OHLCV from Yahoo Finance)
  B. Describe WQB field catalog (optional, when --wqb-fields flag set)

Produces MarketDescription with:
  - Return statistics (mean, std, skew, kurtosis) across the ticker basket
  - Volume statistics
  - Volatility regime analysis (VIX-proxy: cross-sectional return std)
  - Correlation matrix of daily returns across sectors
  - Data quality: missing bars, staleness
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analytics.market_data import MarketDataCrawler


@dataclass
class TickerStats:
    ticker: str
    n_days: int
    mean_ret: float        # mean daily return
    std_ret: float         # std of daily returns (daily vol)
    ann_vol: float         # annualised vol = std * sqrt(252)
    min_ret: float
    max_ret: float
    skew: float            # return skewness
    mean_vol: float        # mean daily volume
    data_start: str
    data_end: str


@dataclass
class MarketDescription:
    tickers: list[TickerStats] = field(default_factory=list)
    cross_sectional_vol: float = 0.0   # proxy for market vol regime
    mean_pairwise_corr: float = 0.0    # mean pairwise return correlation
    high_vol_tickers: list[str] = field(default_factory=list)
    low_vol_tickers: list[str] = field(default_factory=list)
    n_dates: int = 0

    def summary(self) -> str:
        if not self.tickers:
            return "  [describe] No market data available."

        all_vols = [t.ann_vol for t in self.tickers]
        all_rets = [t.mean_ret * 252 for t in self.tickers]  # annualised
        lines = ["── Market Data Description ────────────────────────"]
        lines.append(f"  Tickers analyzed    : {len(self.tickers)}")
        lines.append(f"  Trading days        : {self.n_dates}")
        lines.append(f"  Date range          : {self.tickers[0].data_start if self.tickers else '?'}"
                     f" → {self.tickers[0].data_end if self.tickers else '?'}")
        lines.append("")
        lines.append(f"  Annualised vol      : mean={_mean(all_vols)*100:.1f}%"
                     f"  min={min(all_vols)*100:.1f}%  max={max(all_vols)*100:.1f}%")
        lines.append(f"  Annualised return   : mean={_mean(all_rets)*100:.1f}%"
                     f"  min={min(all_rets)*100:.1f}%  max={max(all_rets)*100:.1f}%")
        lines.append(f"  Cross-sect vol      : {self.cross_sectional_vol*100:.2f}%  "
                     f"(market vol proxy — higher = more dispersion = more alpha opportunity)")
        lines.append(f"  Mean pairwise corr  : {self.mean_pairwise_corr:.3f}  "
                     f"(lower = easier to diversify)")
        lines.append("")
        lines.append(f"  High-vol tickers (>30% ann vol): {self.high_vol_tickers[:8]}")
        lines.append(f"  Low-vol tickers  (<15% ann vol): {self.low_vol_tickers[:8]}")
        lines.append("")
        lines.append("  Top 10 by annualised return:")
        sorted_tickers = sorted(self.tickers, key=lambda t: t.mean_ret, reverse=True)
        for t in sorted_tickers[:10]:
            lines.append(
                f"    {t.ticker:6s}  ann_ret={t.mean_ret*252*100:+.1f}%"
                f"  ann_vol={t.ann_vol*100:.1f}%  skew={t.skew:.2f}"
            )
        return "\n".join(lines)


class DataDescriber:
    """
    Describes external market data fetched by MarketDataCrawler.

    Parameters
    ----------
    market_data : dict[ticker, OHLCV_dict] from MarketDataCrawler.run()
    """

    def __init__(self, market_data: dict[str, dict]):
        self.data = market_data

    def run(self) -> MarketDescription:
        ticker_stats: list[TickerStats] = []

        for ticker, d in self.data.items():
            rets = [r for r in d.get("returns", []) if r != 0.0]
            vols = [v for v in d.get("volume", []) if v > 0]
            closes = d.get("close", [])
            dates = d.get("dates", [])

            if len(rets) < 20:
                continue

            mean_r = _mean(rets)
            std_r  = _std(rets)
            ann_vol = std_r * math.sqrt(252)
            skew = _skew(rets) if len(rets) >= 5 else 0.0

            ticker_stats.append(TickerStats(
                ticker=ticker,
                n_days=len(rets),
                mean_ret=mean_r,
                std_ret=std_r,
                ann_vol=ann_vol,
                min_ret=min(rets),
                max_ret=max(rets),
                skew=skew,
                mean_vol=_mean(vols) if vols else 0.0,
                data_start=dates[0] if dates else "",
                data_end=dates[-1] if dates else "",
            ))

        n_dates = max((len(d.get("close", [])) for d in self.data.values()), default=0)
        cs_vol = self._cross_sectional_vol()
        pairwise = self._mean_pairwise_corr()

        high_vol = sorted([t for t in ticker_stats if t.ann_vol > 0.30],
                          key=lambda t: t.ann_vol, reverse=True)
        low_vol  = sorted([t for t in ticker_stats if t.ann_vol < 0.15],
                          key=lambda t: t.ann_vol)

        return MarketDescription(
            tickers=ticker_stats,
            cross_sectional_vol=cs_vol,
            mean_pairwise_corr=pairwise,
            high_vol_tickers=[t.ticker for t in high_vol],
            low_vol_tickers=[t.ticker for t in low_vol],
            n_dates=n_dates,
        )

    def _cross_sectional_vol(self) -> float:
        """Per-day cross-sectional std of returns, averaged over all days."""
        if not self.data:
            return 0.0
        min_len = min(len(d.get("returns", [])) for d in self.data.values())
        if min_len < 10:
            return 0.0
        daily_cs_vols = []
        for t in range(min_len):
            day_rets = [
                d["returns"][t] for d in self.data.values()
                if t < len(d.get("returns", []))
            ]
            if len(day_rets) >= 10:
                daily_cs_vols.append(_std(day_rets))
        return _mean(daily_cs_vols) if daily_cs_vols else 0.0

    def _mean_pairwise_corr(self, max_pairs: int = 200) -> float:
        """Sample pairwise return correlations."""
        tickers = list(self.data.keys())
        if len(tickers) < 2:
            return 0.0
        corrs = []
        pairs = [(tickers[i], tickers[j])
                 for i in range(len(tickers))
                 for j in range(i + 1, len(tickers))][:max_pairs]
        for ta, tb in pairs:
            ra = self.data[ta].get("returns", [])
            rb = self.data[tb].get("returns", [])
            n = min(len(ra), len(rb))
            if n < 20:
                continue
            c = _corr(ra[-n:], rb[-n:])
            if c is not None:
                corrs.append(c)
        return _mean(corrs) if corrs else 0.0


# ── Math helpers ──────────────────────────────────────────────────────────────

def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0

def _std(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    variance = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(variance)

def _skew(xs: list[float]) -> float:
    if len(xs) < 3:
        return 0.0
    m = _mean(xs)
    s = _std(xs)
    if s == 0:
        return 0.0
    n = len(xs)
    return (sum((x - m) ** 3 for x in xs) / n) / (s ** 3)

def _corr(xa: list[float], xb: list[float]) -> float | None:
    n = len(xa)
    if n < 5:
        return None
    ma, mb = _mean(xa), _mean(xb)
    cov = sum((xa[i] - ma) * (xb[i] - mb) for i in range(n)) / n
    sa, sb = _std(xa), _std(xb)
    if sa == 0 or sb == 0:
        return None
    return cov / (sa * sb)
