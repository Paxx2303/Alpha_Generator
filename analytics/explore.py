"""
analytics/explore.py — Step 2: Understand Data

Two sub-analyses:

A. IC Analysis on real market data (Signal IC = Information Coefficient)
   - For each candidate signal, compute cross-sectional Pearson correlation
     between signal value (today) and 1-day/5-day forward return
   - Mean IC, IC/std (t-stat), Hit Rate
   - Signals: momentum, reversal, volume, vol-adjusted reversal, etc.

B. WQB History Mining (mine wqb_data.db)
   - Which settings (universe/neut/decay) maximise mean Sharpe
   - Which operators appear most in winning formulas

Output: PatternReport
"""
from __future__ import annotations

import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# ── Signal definitions ────────────────────────────────────────────────────────
# Each signal is computed from OHLCV dict. Function signature:
#   f(close, returns, volume, high, low) -> list[float] (same length as close)
# Returns NaN-padded for lookback periods.

NAN = float("nan")


def _roll_mean(xs, n):
    out = [NAN] * len(xs)
    for i in range(n - 1, len(xs)):
        out[i] = sum(xs[i - n + 1: i + 1]) / n
    return out

def _roll_std(xs, n):
    out = [NAN] * len(xs)
    for i in range(n - 1, len(xs)):
        window = xs[i - n + 1: i + 1]
        m = sum(window) / n
        var = sum((x - m) ** 2 for x in window) / (n - 1) if n > 1 else 0
        out[i] = math.sqrt(var)
    return out

def _rank_pct(xs: list[float]) -> list[float]:
    """Cross-sectional percentile rank, ignoring NaN."""
    valid = [(v, i) for i, v in enumerate(xs) if not math.isnan(v)]
    if not valid:
        return [NAN] * len(xs)
    sorted_v = sorted(valid, key=lambda t: t[0])
    ranks = [NAN] * len(xs)
    n = len(sorted_v)
    for rank, (_, idx) in enumerate(sorted_v):
        ranks[idx] = (rank + 1) / n
    return ranks


SIGNALS: dict[str, dict] = {
    # ── Proven microstructure signals (from WQB sims) ─────────────────────
    "intraday_ret": {
        "desc": "Intraday return (close vs open) — WQB proven S=1.84",
        "wqb": "(close - open) / (open + 0.001)",
        "compute": lambda c, r, v, h, l, o: [
            (c[i] - o[i]) / (o[i] + 1e-8) for i in range(len(c))
        ],
    },
    "intraday_smooth3": {
        "desc": "3d smoothed intraday return — near-pass F=0.92",
        "wqb": "ts_mean((close - open) / (open + 0.001), 3)",
        "compute": lambda c, r, v, h, l, o: _roll_mean(
            [(c[i] - o[i]) / (o[i] + 1e-8) for i in range(len(c))], 3
        ),
    },
    "vwap_dev_5d": {
        "desc": "5d VWAP deviation — WQB proven S=1.65, F=1.16 PASS",
        "wqb": "(close - ts_sum(close*volume,5)/(ts_sum(volume,5)+1)) / (close+0.001)",
        "compute": lambda c, r, v, h, l, o: [
            (c[i] - (sum(c[j]*v[j] for j in range(max(0,i-4),i+1)) /
                     (sum(v[j] for j in range(max(0,i-4),i+1)) + 1))) / (c[i] + 1e-8)
            if i >= 4 else NAN
            for i in range(len(c))
        ],
    },
    "overnight_ret": {
        "desc": "Overnight return (open vs prev close) — complement to intraday",
        "wqb": "(open - ts_delay(close, 1)) / (ts_delay(close, 1) + 0.001)",
        "compute": lambda c, r, v, h, l, o: [
            (o[i] - c[i-1]) / (c[i-1] + 1e-8) if i >= 1 else NAN
            for i in range(len(c))
        ],
    },
    "close_location": {
        "desc": "Where close sits in high-low range (0=low, 1=high)",
        "wqb": "(close - low) / (high - low + 0.001)",
        "compute": lambda c, r, v, h, l, o: [
            (c[i] - l[i]) / (h[i] - l[i] + 1e-8) for i in range(len(c))
        ],
    },
    "vol_price_diverge": {
        "desc": "Volume-price divergence: high vol + small price move = informed",
        "wqb": "volume / (ts_mean(volume,20)+1) / (abs(returns)+0.001)",
        "compute": lambda c, r, v, h, l, o: [
            (v[i] / (sum(v[max(0,i-20):i]) / max(min(i,20),1) + 1)) / (abs(r[i]) + 1e-3)
            if i >= 5 else NAN
            for i in range(len(c))
        ],
    },
    # ── Classic reversal / momentum signals ──────────────────────────────
    "ret_1d": {
        "desc": "1-day return reversal",
        "wqb": "ts_delta(close, 1) / close",
        "compute": lambda c, r, v, h, l, o: r,
    },
    "reversal_5d": {
        "desc": "5-day price reversal (Jegadeesh 1990)",
        "wqb": "-ts_delta(close, 5) / (close + 0.001)",
        "compute": lambda c, r, v, h, l, o: [
            -(c[i] - c[i - 5]) / (c[i - 5] + 1e-8) if i >= 5 else NAN
            for i in range(len(c))
        ],
    },
    "momentum_20d": {
        "desc": "20-day price momentum (Jegadeesh-Titman 1993)",
        "wqb": "ts_delta(close, 20) / (close + 0.001)",
        "compute": lambda c, r, v, h, l, o: [
            (c[i] - c[i - 20]) / (c[i - 20] + 1e-8) if i >= 20 else NAN
            for i in range(len(c))
        ],
    },
    "vol_adj_reversal_2d": {
        "desc": "Vol-normalised 2-day reversal (Pattern A core)",
        "wqb": "-ts_delta(close, 2) / (ts_std_dev(returns, 20) * close + 0.001)",
        "compute": lambda c, r, v, h, l, o: [
            -((c[i] - c[i - 2]) / (c[i - 2] + 1e-8)) / (_std_local(r, i, 20) + 1e-8)
            if i >= 20 else NAN
            for i in range(len(c))
        ],
    },
    "volume_surge_5d": {
        "desc": "Volume vs 20d average (liquidity signal)",
        "wqb": "volume / (ts_mean(volume, 20) + 1)",
        "compute": lambda c, r, v, h, l, o: [
            v[i] / (sum(v[max(0, i - 20): i]) / max(min(i, 20), 1) + 1)
            if i >= 5 else NAN
            for i in range(len(c))
        ],
    },
    "price_range_10d": {
        "desc": "Price range / price (volatility of price levels)",
        "wqb": "(ts_max(close, 10) - ts_min(close, 10)) / (close + 0.001)",
        "compute": lambda c, r, v, h, l, o: [
            (max(c[max(0, i - 10): i + 1]) - min(c[max(0, i - 10): i + 1])) / (c[i] + 1e-8)
            if i >= 10 else NAN
            for i in range(len(c))
        ],
    },
    "high_low_pct": {
        "desc": "Intraday range: (high - low) / close",
        "wqb": "(high - low) / (close + 0.001)",
        "compute": lambda c, r, v, h, l, o: [
            (h[i] - l[i]) / (c[i] + 1e-8) for i in range(len(c))
        ],
    },
    "52w_high_proximity": {
        "desc": "Distance from 52-week high (George-Hwang 2004)",
        "wqb": "-(close / (ts_max(close, 252) + 0.001))",
        "compute": lambda c, r, v, h, l, o: [
            -(c[i] / (max(c[max(0, i - 252): i + 1]) + 1e-8))
            if i >= 20 else NAN
            for i in range(len(c))
        ],
    },
    "amihud_illiq_20d": {
        "desc": "Amihud illiquidity (|ret|/volume) 20d mean",
        "wqb": "ts_mean(abs(returns) / (volume * close + 1), 20)",
        "compute": lambda c, r, v, h, l, o: [
            sum(abs(r[j]) / (v[j] * c[j] + 1) for j in range(max(0, i - 20), i + 1)) / min(i + 1, 20)
            if i >= 5 else NAN
            for i in range(len(c))
        ],
    },
}


def _std_local(xs, i, n):
    window = xs[max(0, i - n): i + 1]
    if len(window) < 2:
        return 0.0
    m = sum(window) / len(window)
    return math.sqrt(sum((x - m) ** 2 for x in window) / (len(window) - 1))


@dataclass
class SignalIC:
    name: str
    description: str
    wqb_formula: str
    mean_ic_1d: float     # mean IC predicting 1-day fwd return
    ic_std_1d: float
    icir_1d: float        # IC / std = information ratio
    mean_ic_5d: float     # mean IC predicting 5-day fwd return
    ic_std_5d: float
    icir_5d: float
    hit_rate_1d: float    # fraction of days where IC > 0


@dataclass
class PatternReport:
    # IC analysis on real market data
    signal_ics: list[SignalIC] = field(default_factory=list)
    top_signals: list[SignalIC] = field(default_factory=list)   # |ICIR| >= 0.5

    # WQB history mining
    total_wqb_sims: int = 0
    wqb_pass_rate: float = 0.0
    best_settings: list[dict] = field(default_factory=list)
    sharpe_by_neutralization: dict[str, float] = field(default_factory=dict)
    sharpe_by_universe: dict[str, float] = field(default_factory=dict)
    top_operators: list[tuple[str, int]] = field(default_factory=list)

    def summary(self) -> str:
        lines = ["── Pattern Report ─────────────────────────────────"]

        if self.signal_ics:
            lines.append("  Signal IC Analysis (real market data):")
            lines.append(f"  {'Signal':25s}  {'IC_1d':>7s}  {'ICIR_1d':>7s}  {'IC_5d':>7s}  {'ICIR_5d':>7s}  {'Hit%':>5s}  WQB Formula")
            lines.append("  " + "-" * 95)
            for sig in sorted(self.signal_ics, key=lambda s: abs(s.icir_1d), reverse=True):
                flag = " <<< STRONG" if abs(sig.icir_1d) >= 0.5 else ""
                lines.append(
                    f"  {sig.name:25s}  {sig.mean_ic_1d:+.4f}  {sig.icir_1d:+.4f}"
                    f"  {sig.mean_ic_5d:+.4f}  {sig.icir_5d:+.4f}"
                    f"  {sig.hit_rate_1d*100:5.1f}%"
                    f"  {sig.wqb_formula[:50]}{flag}"
                )

        if self.total_wqb_sims > 0:
            lines.append(f"\n  WQB Simulation History ({self.total_wqb_sims} sims, pass={self.wqb_pass_rate*100:.1f}%):")
            lines.append("  Best settings (mean Sharpe):")
            for s in self.best_settings[:5]:
                lines.append(
                    f"    {s['universe']:8s}|{s['neutralization']:12s}"
                    f"|Decay={s['decay']:2d}  → mean_S={s['mean_sharpe']:.2f}  (n={s['count']})"
                )
            lines.append("  Top operators in winning formulas:")
            for op, cnt in self.top_operators[:8]:
                lines.append(f"    {op:25s} : {cnt}")

        return "\n".join(lines)


class DataExplorer:
    """
    Runs two analyses:
      1. IC analysis on real OHLCV market data
      2. WQB simulation history mining

    Parameters
    ----------
    market_data : dict[ticker, OHLCV] from MarketDataCrawler
    wqb_db_path : path to wqb_data.db
    fwd_days    : forward return window for IC (default 1 and 5)
    """

    WQB_OPERATORS = [
        "ts_rank", "ts_delta", "ts_mean", "ts_std_dev", "ts_max", "ts_min",
        "ts_sum", "ts_corr", "ts_backfill", "ts_delay",
        "rank", "group_rank", "group_neutralize",
        "trade_when", "winsorize",
    ]
    # WQB FIELD names (lowercase, underscored) — used to exclude comment words
    WQB_FIELDS = {
        "close", "open", "high", "low", "volume", "returns", "vwap",
        "adv20", "adv5", "cap", "sales", "assets", "equity",
        "est_sales", "book_value", "earnings",
    }

    def __init__(
        self,
        market_data: dict[str, dict] | None = None,
        wqb_db_path: str | Path | None = None,
        sharpe_pass: float = 1.25,
    ):
        self.market_data = market_data or {}
        self.wqb_db_path = Path(wqb_db_path) if wqb_db_path else None
        self.sharpe_pass = sharpe_pass

    def run(self) -> PatternReport:
        report = PatternReport()

        if self.market_data:
            print("  [explore] Computing signal ICs on real market data...")
            report.signal_ics = self._compute_ics()
            report.top_signals = [s for s in report.signal_ics if abs(s.icir_1d) >= 0.5]

        if self.wqb_db_path and self.wqb_db_path.exists():
            print(f"  [explore] Mining WQB history from {self.wqb_db_path.name}...")
            self._mine_wqb_history(report)

        return report

    # ── IC Analysis ──────────────────────────────────────────────────────────

    def _compute_ics(self) -> list[SignalIC]:
        # Build panel: for each date, list of (signal_value, fwd_ret_1d, fwd_ret_5d) per ticker
        all_dates = sorted(set(
            d for ticker_d in self.market_data.values()
            for d in ticker_d.get("dates", [])
        ))

        # Align tickers to common date index
        date_idx = {d: i for i, d in enumerate(all_dates)}
        n_dates = len(all_dates)

        # Pre-compute signal arrays per ticker
        sig_arrays: dict[str, dict[str, list[float]]] = {}  # ticker -> signal_name -> values

        for ticker, d in self.market_data.items():
            dates = d.get("dates", [])
            c = d.get("close", [])
            r = d.get("returns", [])
            v = d.get("volume", [])
            h = d.get("high", c)
            lo = d.get("low", c)
            o = d.get("open", c)
            n = len(c)

            ticker_sigs: dict[str, list[float]] = {}
            for sig_name, sig_def in SIGNALS.items():
                try:
                    vals = sig_def["compute"](c, r, v, h, lo, o)
                    ticker_sigs[sig_name] = vals
                except Exception:
                    ticker_sigs[sig_name] = [NAN] * n

            # Forward returns
            fwd1 = [r[i + 1] if i + 1 < n else NAN for i in range(n)]
            fwd5 = [(c[i + 5] - c[i]) / (c[i] + 1e-8) if i + 5 < n else NAN for i in range(n)]
            ticker_sigs["__fwd1"] = fwd1
            ticker_sigs["__fwd5"] = fwd5
            ticker_sigs["__date_offset"] = [date_idx.get(dates[i], -1) for i in range(n)]
            sig_arrays[ticker] = ticker_sigs

        # Build daily cross-sections: for each date, list of (sig_val, fwd1, fwd5) per ticker
        daily_cross: list[dict[str, list]] = []  # list of {sig_name: [vals across tickers]}
        for day_i in range(n_dates - 5):  # leave room for 5d fwd
            day_sigs: dict[str, list] = {name: [] for name in SIGNALS}
            day_fwd1: list[float] = []
            day_fwd5: list[float] = []

            for ticker, ts in sig_arrays.items():
                offsets = ts.get("__date_offset", [])
                # Find this ticker's index for day_i
                try:
                    local_i = offsets.index(day_i) if day_i in offsets else -1
                except ValueError:
                    local_i = -1

                if local_i < 0:
                    continue

                f1 = ts["__fwd1"][local_i]
                f5 = ts["__fwd5"][local_i]
                if math.isnan(f1) or math.isnan(f5):
                    continue

                valid = True
                for sig_name in SIGNALS:
                    val = ts.get(sig_name, [NAN] * (local_i + 1))[local_i]
                    if math.isnan(val):
                        valid = False
                        break
                    day_sigs[sig_name].append(val)

                if valid:
                    day_fwd1.append(f1)
                    day_fwd5.append(f5)

            if len(day_fwd1) >= 10:  # need enough cross-section
                daily_cross.append({
                    "sigs": day_sigs,
                    "fwd1": day_fwd1,
                    "fwd5": day_fwd5,
                })

        # Compute IC per day per signal
        sig_ics_1d: dict[str, list[float]] = {s: [] for s in SIGNALS}
        sig_ics_5d: dict[str, list[float]] = {s: [] for s in SIGNALS}

        for dc in daily_cross:
            fwd1 = dc["fwd1"]
            fwd5 = dc["fwd5"]
            for sig_name in SIGNALS:
                sv = dc["sigs"][sig_name]
                if len(sv) != len(fwd1) or len(sv) < 5:
                    continue
                c1 = _pearson(sv, fwd1)
                c5 = _pearson(sv, fwd5)
                if c1 is not None:
                    sig_ics_1d[sig_name].append(c1)
                if c5 is not None:
                    sig_ics_5d[sig_name].append(c5)

        # Summarise
        results = []
        for sig_name, sig_def in SIGNALS.items():
            ics1 = sig_ics_1d.get(sig_name, [])
            ics5 = sig_ics_5d.get(sig_name, [])
            if not ics1:
                continue
            mean1 = _mean(ics1)
            std1  = _std(ics1) or 1e-8
            mean5 = _mean(ics5) if ics5 else 0.0
            std5  = _std(ics5) or 1e-8
            hit1  = sum(1 for ic in ics1 if ic > 0) / len(ics1)
            results.append(SignalIC(
                name=sig_name,
                description=sig_def["desc"],
                wqb_formula=sig_def["wqb"],
                mean_ic_1d=mean1,
                ic_std_1d=std1,
                icir_1d=mean1 / std1,
                mean_ic_5d=mean5,
                ic_std_5d=std5,
                icir_5d=mean5 / std5 if std5 > 0 else 0,
                hit_rate_1d=hit1,
            ))

        return sorted(results, key=lambda s: abs(s.icir_1d), reverse=True)

    # ── WQB History Mining ───────────────────────────────────────────────────

    def _mine_wqb_history(self, report: PatternReport):
        conn = sqlite3.connect(self.wqb_db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT formula, settings, sharpe FROM alpha_results WHERE sharpe IS NOT NULL"
        ).fetchall()
        conn.close()

        if not rows:
            return

        report.total_wqb_sims = len(rows)
        winners = [r for r in rows if r["sharpe"] >= self.sharpe_pass]
        report.wqb_pass_rate = len(winners) / len(rows)

        # Settings analysis
        bucket: dict[tuple, list[float]] = {}
        univ_s: dict[str, list[float]] = {}
        neut_s: dict[str, list[float]] = {}
        for r in rows:
            parts = (r["settings"] or "").split("|")
            if len(parts) >= 3:
                u, n = parts[0], parts[1]
                try:
                    d = int(parts[2])
                except ValueError:
                    d = 0
                bucket.setdefault((u, n, d), []).append(r["sharpe"])
                univ_s.setdefault(u, []).append(r["sharpe"])
                neut_s.setdefault(n, []).append(r["sharpe"])

        report.best_settings = sorted(
            [{"universe": k[0], "neutralization": k[1], "decay": k[2],
              "mean_sharpe": _mean(v), "count": len(v)}
             for k, v in bucket.items() if len(v) >= 2],
            key=lambda x: x["mean_sharpe"], reverse=True,
        )
        report.sharpe_by_universe = {k: _mean(v) for k, v in univ_s.items()}
        report.sharpe_by_neutralization = {k: _mean(v) for k, v in neut_s.items()}

        # Operator analysis (winning formulas only)
        op_counts: Counter[str] = Counter()
        for r in winners:
            formula = (r["formula"] or "").lower()
            for op in self.WQB_OPERATORS:
                if op + "(" in formula:
                    op_counts[op] += 1
        report.top_operators = op_counts.most_common()


# ── Math helpers ──────────────────────────────────────────────────────────────

def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0

def _std(xs):
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

def _pearson(xs, ys):
    n = len(xs)
    if n < 5:
        return None
    mx, my = _mean(xs), _mean(ys)
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / n
    sx = _std(xs)
    sy = _std(ys)
    if sx == 0 or sy == 0:
        return None
    return cov / (sx * sy)
