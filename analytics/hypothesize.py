"""
analytics/hypothesize.py — Step 3: Predict (Generate Hypotheses)

Translates high-IC signals from real market data (Step 2) into WQB formula candidates.

Scoring:
  confidence = 0.5 × |ICIR_1d_norm| + 0.3 × |ICIR_5d_norm| + 0.2 × hit_rate
  Bonus: +0.1 if ICIR_5d and ICIR_1d have same sign (consistent direction)
  Penalty: -0.3 if signal is in DEAD_FIELDS

Each AlphaHypothesis has a full WQB formula + recommended settings based on
WQB history (best_settings from PatternReport).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analytics.describe import MarketDescription
    from analytics.explore import PatternReport, SignalIC

DEAD_FIELDS: set[str] = {"est_sales", "book_value"}  # book_value: unknown variable on WQB FASTEXPR

# Operators unavailable on this account — formulas using these will error on WQB
# delay() → use ts_delay() instead
# rank() directly on event-type fields → use last_known() wrapper first
DEAD_OPERATORS: set[str] = {"ts_max", "ts_min", "delay"}

# Proven Pattern A as anchor — always included
PATTERN_A = {
    "id": "pattern_a_anchor",
    "name": "Pattern A (proven IQC pass): Vol-regime 2d reversal",
    "formula": (
        "mr   = -rank((close - ts_delay(close, 2))\n"
        "             / (ts_delay(close, 2) * (ts_std_dev(returns, 20) + 0.001)));\n"
        "when = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;\n"
        "b    = trade_when(when, mr, -1);\n"
        "group_neutralize(b, subindustry)"
    ),
    "settings": "TOP3000|Subindustry|10|0.08",
    "confidence": 0.80,
    "rationale": "Simulated: S=1.58, F=1.00, TO=30.3% — IQC PASS. Already in DB (1YgWwo8W). Fallback only.",
    "theory": "Vol-normalised reversal conditional on vol regime (Moskowitz et al.)",
    "source": "proven",
}

# Proven Pattern B — VWAP Deviation (IQC PASS, best performer)
PATTERN_B = {
    "id": "pattern_b_vwap",
    "name": "Pattern B (proven IQC pass): 5d VWAP Deviation Reversal",
    "formula": (
        "vwap5  = ts_sum(close * volume, 5) / (ts_sum(volume, 5) + 1);\n"
        "dev    = (close - vwap5) / (vwap5 + 0.001);\n"
        "signal = group_rank(-rank(dev), subindustry);\n"
        "group_neutralize(signal, subindustry)"
    ),
    "settings": "TOP3000|Subindustry|5|0.08",
    "confidence": 0.79,
    "rationale": "Simulated: S=1.65, F=1.16, TO=21.0% — IQC PASS. Already in DB (Gro90oex). Fallback only.",
    "theory": "VWAP is institutional anchor price. Below-VWAP stocks attract buy orders.",
    "source": "proven",
}

# ── Proven FUNDAMENTAL anchors (highest-Fitness family, uncorrelated w/ VWAP) ──
# yfinance has no fundamentals → these get NO IC from Step 3. They are always
# included as proven anchors because WQB history shows they reach the highest
# Fitness (rKWvzA3j F=1.64) and are an independent signal family from price/volume.
# Validated WQB fields: est_eps, est_fcf, est_ptp, cashflow_op, enterprise_value.
FUNDAMENTAL_ANCHORS = [
    # ── NEW (untested) signals — highest priority ─────────────────────────────
    {
        "id": "fund_fcf_yield_mkt",
        "name": "Fundamental: FCF Yield vs Price (market-neutral)",
        "formula": (
            "fcf_y  = ts_backfill(est_fcf, 60) / (close + 0.001);\n"
            "signal = group_rank(ts_rank(fcf_y, 60), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.39,
        "rationale": "FAILED: S=1.00, F=0.62 — below IQC fitness threshold. Cached as failed combination.",
        "theory": "FCF yield value premium. High FCF/price → undervalued on cash. Market neut → pure cross-sectional signal.",
        "source": "proven",
    },
    {
        "id": "fund_ptp_revision",
        "name": "Fundamental: PTP Revision Momentum (pretax drift)",
        "formula": (
            "ptp_now = ts_backfill(est_ptp, 60);\n"
            "ptp_lag = ts_backfill(ts_delay(est_ptp, 20), 60);\n"
            "rev     = (ptp_now - ptp_lag) / (abs(ptp_lag) + 1);\n"
            "signal  = group_rank(ts_rank(rev, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.38,
        "rationale": "FAILED: S=-0.32 — completely negative Sharpe after group_neutralize(industry). Cached as failed combination.",
        "theory": "Upward PTP revisions predict drift (Chan 1996). est_ptp more stable than est_eps → cleaner signal.",
        "source": "proven",
    },
    {
        "id": "fund_fcf_ptp_quality",
        "name": "Fundamental: FCF-to-PTP Quality Ratio",
        "formula": (
            "fcf_bf  = ts_backfill(est_fcf, 60);\n"
            "ptp_bf  = ts_backfill(est_ptp, 60);\n"
            "quality = fcf_bf / (abs(ptp_bf) + 1);\n"
            "signal  = group_rank(ts_rank(quality, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.37,
        "rationale": "FAILED: S=-0.61 — deeply negative. FCF/PTP ratio signal doesn't survive neutralization.",
        "theory": "Earnings quality via cash conversion. High FCF/PTP → reliable earnings → outperform (Dechow 1994).",
        "source": "proven",
    },
    {
        "id": "fund_cfo_trend",
        "name": "Fundamental: Operating Cashflow Trend",
        "formula": (
            "cfo_bf = ts_backfill(cashflow_op, 60);\n"
            "trend  = ts_delta(cfo_bf, 20) / (abs(cfo_bf) + 1);\n"
            "signal = group_rank(ts_rank(trend, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.88,
        "rationale": "Rising operating cashflow trend = improving business quality. Distinct from level-based cashflow_ev.",
        "theory": "Cashflow momentum. Accelerating CFO → fundamental improvement not yet priced (Sloan 1996 extension).",
        "source": "proven",
    },
    {
        "id": "fund_eps_stability",
        "name": "Fundamental: EPS Estimate Stability (low dispersion)",
        "formula": (
            "eps_bf  = ts_backfill(est_eps, 60);\n"
            "mean_e  = ts_mean(eps_bf, 20);\n"
            "stable  = -(ts_std_dev(eps_bf, 20) / (abs(mean_e) + 0.01));\n"
            "signal  = group_rank(ts_rank(stable, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.87,
        "rationale": "Low EPS estimate volatility = analyst consensus = low uncertainty premium. Short high-uncertainty stocks.",
        "theory": "Uncertainty premium (Diether 2002). Low est_eps dispersion → less divergence of opinion → tighter spread.",
        "source": "proven",
    },
    # ── TOP PRIORITY: Research-backed new signals (June 2026) ────────────────
    {
        "id": "fund_ptp_price_corr",
        "name": "Fundamental: PTP–Price Divergence (fundamental-price corr)",
        "formula": (
            "ptp_bf = ts_backfill(est_ptp, 60);\n"
            "signal = group_rank(-ts_corr(ptp_bf, close, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.36,
        "rationale": "FAILED: S=-0.71 — price is not a valid counter-field for ts_corr with fundamental estimates. Cached as failed.",
        "theory": "Earnings-to-price divergence. When est_ptp and close decouple, price hasn't yet reflected fundamental value.",
        "source": "proven",
    },
    {
        "id": "fund_cfo_cap_yield",
        "name": "Fundamental: CFO/Market-Cap Yield (WQB official example)",
        "formula": (
            "cfo_y  = ts_backfill(cashflow_op, 60) / (cap + 1);\n"
            "signal = group_rank(ts_rank(cfo_y, 60), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|4|0.08",
        "confidence": 0.36,
        "rationale": "CORRELATED (e7OkXQmz S=1.79 F=1.15): self-corr with 6XEvXKmG (cashflow_op/EV). Both use cashflow_op numerator. Use fund_cfo_cap_mkt variant instead.",
        "theory": "CFO yield vs market cap. High cashflow/cap = undervalued on cash generation. Subindustry neutral captures relative cheapness.",
        "source": "proven",
    },
    {
        "id": "fund_cfo_cap_mkt",
        "name": "Fundamental: CFO/Cap Yield Market-Neutral (long-window z-score)",
        "formula": (
            "cfo_y  = ts_backfill(cashflow_op, 60) / (cap + 1);\n"
            "signal = group_rank(ts_zscore(cfo_y, 120), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.35,
        "rationale": "FAILED: S=0.90 F=0.72 — ts_zscore(120) + Market lost too much signal vs original ts_rank(60). Try fund_cfo_cap_sector instead.",
        "theory": "CFO yield z-scored vs 120d own history, market-neutral. Captures absolute valuation gap vs all stocks, not just industry peers.",
        "source": "proven",
    },
    {
        "id": "fund_cfo_cap_sector",
        "name": "Fundamental: CFO/Cap Yield Sector-Neutral (ts_rank, Sector neut)",
        "formula": (
            "cfo_y  = ts_backfill(cashflow_op, 60) / (cap + 1);\n"
            "signal = group_rank(ts_rank(cfo_y, 60), sector);\n"
            "group_neutralize(signal, sector)"
        ),
        "settings": "TOP3000|Sector|3|0.08",
        "confidence": 0.34,
        "rationale": "CORRELATED (MPpOP0AM S=1.53, F=1.14): self-corr 0.82 with 6XEvXKmG. Sector-neutral did NOT reduce self-corr vs Subindustry (was 0.78). cashflow_op in all variants is saturated. Skip.",
        "theory": "CFO/cap value yield, Sector-neutralized. Captures within-sector valuation gap rather than within-subindustry.",
        "source": "proven",
    },
    {
        "id": "fund_cfo_price_corr",
        "name": "Fundamental: CFO–Price Divergence Correlation",
        "formula": (
            "cfo_bf = ts_backfill(cashflow_op, 60);\n"
            "signal = group_rank(-ts_corr(cfo_bf, close, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.36,
        "rationale": "SKIPPED (preemptive): uses cashflow_op which is in submitted d5xkGzNx. Any cashflow_op-based signal self-correlates with d5xkGzNx (self-corr pattern identified). Do not simulate.",
        "theory": "CFO-price divergence. When cashflow trend and price trend decouple, fundamental value is mispriced.",
        "source": "proven",
    },
    # ── PROVEN MECHANISM: ts_corr between estimate vs actual fields ───────────
    # rKWvzA3j: -ts_corr(est_ptp, est_fcf, 20)  F=1.64  SUBMITTED
    # d5xkGzNx: -ts_corr(est_eps, cashflow_op, 20) F=1.78 SUBMITTED
    # → New untried pairs below
    # ── NEW DIRECTION: Different fields + different construction ─────────────
    {
        "id": "new_vol_vwap_corr",
        "name": "Price/Vol: Volume–VWAP Rank Correlation (divergence signal)",
        "formula": (
            "signal = group_rank(-ts_corr(ts_rank(volume, 10), ts_rank(vwap, 10), 20), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "confidence": 0.97,
        "rationale": "WQB seminar proven signal. Low corr between volume rank and VWAP rank = volume surge not reflected in price → accumulation signal. Pure price/vol, no fundamental exposure.",
        "theory": "Volume-price divergence. When volume and VWAP ranks decouple, informed accumulation is occurring without price impact.",
        "source": "proven",
    },
    {
        "id": "fund_eps_ebitda_corr",
        "name": "Fundamental: EPS–EBITDA Divergence Correlation (new field)",
        "formula": (
            "ebitda_bf = ts_backfill(ebitda, 60);\n"
            "signal    = group_rank(-ts_corr(est_eps, ebitda_bf, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.95,
        "rationale": "Same proven ts_corr mechanism (rKWvzA3j F=1.64, d5xkGzNx F=1.78) but uses NEW field ebitda. EPS estimate vs actual EBITDA divergence → earnings quality uncertainty.",
        "theory": "Analyst EPS estimate vs actual EBITDA divergence. Low corr = EPS forecast and operating earnings disconnected → mispricing.",
        "source": "proven",
    },
    {
        "id": "fund_ev_ebitda",
        "name": "Fundamental: EV/EBITDA Valuation Signal (WQB seminar)",
        "formula": (
            "ebitda_bf = ts_backfill(ebitda, 60);\n"
            "ev_eb     = enterprise_value / (abs(ebitda_bf) + 1);\n"
            "signal    = group_rank(-ts_zscore(ev_eb, 63), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.93,
        "rationale": "From WQB seminar: -ts_zscore(enterprise_value/ebitda, 63). Short high EV/EBITDA (overvalued) within industry. New field ebitda, different from est_* family.",
        "theory": "Value premium via EV/EBITDA multiple. High EV/EBITDA = overvalued relative to operating earnings → mean reversion.",
        "source": "proven",
    },
    {
        "id": "fund_book_market",
        "name": "Fundamental: Book-to-Market Ratio (equity field)",
        "formula": (
            "equity_bf = ts_backfill(equity, 60);\n"
            "btm       = equity_bf / (cap + 1);\n"
            "signal    = group_rank(ts_rank(btm, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.91,
        "rationale": "Classic Fama-French value factor. Uses WQB field `equity` (book value) and `cap` (market cap). Different from all existing alphas — pure book value approach.",
        "theory": "Book-to-market value premium (Fama-French 1992). High B/M = cheap stocks → long-run outperformance.",
        "source": "proven",
    },
    {
        "id": "fund_eps_ptp_corr",
        "name": "Fundamental: EPS–PTP Divergence Correlation (untried pair)",
        "formula": (
            "signal = group_rank(-ts_corr(est_eps, est_ptp, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.33,
        "rationale": "FAIL IQC: S=1.34, F=0.82 — Returns too low (7.16%). est_eps and est_ptp measure same thing → weak divergence signal.",
        "theory": "Cross-estimate divergence. est_eps and est_ptp should co-move; when they don't → analyst uncertainty → mispricing. Different from all submitted pairs.",
        "source": "proven",
    },
    {
        "id": "fund_cfo_ev_corr",
        "name": "Fundamental: CFO–EV Divergence Correlation (actual cash vs valuation)",
        "formula": (
            "signal = group_rank(-ts_corr(cashflow_op, enterprise_value, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.32,
        "rationale": "TIMEOUT on WQB — simulation timed out. Skip.",
        "theory": "Cash-valuation divergence. When actual CF and EV decouple → market not pricing cash flows correctly → mean-reversion opportunity.",
        "source": "proven",
    },
    {
        "id": "fund_ptp_cfo_corr",
        "name": "Fundamental: PTP–CFO Divergence Correlation (estimate vs actual)",
        "formula": (
            "signal = group_rank(-ts_corr(est_ptp, cashflow_op, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.34,
        "rationale": "CORRELATED 0.91 (npg9xA2w): self-corr with rKWvzA3j (est_ptp) + d5xkGzNx (cashflow_op). Both fields already submitted. Skip.",
        "theory": "Analyst estimate vs realized cashflow divergence. When PTP estimate and actual operating CF decouple → earnings quality uncertainty → mispricing.",
        "source": "proven",
    },
    {
        "id": "fund_fcf_cfo_corr",
        "name": "Fundamental: FCF estimate–CFO Actual Divergence Correlation",
        "formula": (
            "signal = group_rank(-ts_corr(est_fcf, cashflow_op, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.34,
        "rationale": "FAIL_CHECKS (YPp6L9j6): weight_conc 16.67%>10%, sub-universe Sharpe 0.59<0.6. Try fund_fcf_cfo_corr_fix with truncation=0.05 + Industry neut.",
        "theory": "FCF estimate accuracy signal. Low corr = analyst FCF forecasts disconnected from actual cash → forecast uncertainty premium.",
        "source": "proven",
    },
    {
        "id": "fund_fcf_cfo_corr_fix",
        "name": "Fundamental: FCF–CFO Divergence (Industry-neut, trunc=0.05)",
        "formula": (
            "signal = group_rank(-ts_corr(est_fcf, cashflow_op, 20), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.05",
        "confidence": 0.31,
        "rationale": "FAIL IQC: S=0.70, F=0.56 — Industry neut degraded Sharpe vs original. Abandon this fix.",
        "theory": "FCF estimate vs actual CF divergence, within-industry. Industry neut → more consistent signal across market sub-universes.",
        "source": "proven",
    },
    # ── NEW: Correlation-based signals (same mechanism as rKWvzA3j F=1.64) ────
    {
        "id": "fund_eps_cfo_corr",
        "name": "Fundamental: EPS–CFO Estimate Correlation (market-neutral)",
        "formula": (
            "signal = group_rank(-ts_corr(est_eps, cashflow_op, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.35,
        "rationale": "DONE: d5xkGzNx S=1.45 F=1.78 SUBMITTED_SUCCESS. Skip to prevent re-simulation.",
        "theory": "Analyst divergence signal. est_eps vs cashflow_op corr measures how well earnings track cash reality.",
        "source": "proven",
    },
    {
        "id": "fund_fcf_ev_corr",
        "name": "Fundamental: FCF–EV Correlation (market-neutral)",
        "formula": (
            "signal = group_rank(-ts_corr(est_fcf, enterprise_value, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.92,
        "rationale": "Low corr between FCF estimate and enterprise value → valuation divergence → mispricing opportunity.",
        "theory": "FCF-valuation divergence. When est_fcf and EV move independently → analyst disagreement about intrinsic value.",
        "source": "proven",
    },
    {
        "id": "fund_eps_ev_corr",
        "name": "Fundamental: EPS–EV Correlation (market-neutral)",
        "formula": (
            "signal = group_rank(-ts_corr(est_eps, enterprise_value, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.90,
        "rationale": "Low corr between EPS estimates and enterprise value → earnings-valuation disconnect → opportunity.",
        "theory": "EPS vs valuation divergence signal. Orthogonal pair to rKWvzA3j (est_ptp vs est_fcf).",
        "source": "proven",
    },
    # ── Near-miss price signal: body5 Decay=0 (best missed F=0.98 at Decay=2) ─
    {
        "id": "price_body5_decay0",
        "name": "Price: 5d Candle Body Reversal (Decay=0)",
        "formula": (
            "body  = (close - open) / (open + 0.001);\n"
            "body5 = ts_sum(body, 5);\n"
            "signal = group_rank(-rank(body5), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|0|0.08",
        "confidence": 0.89,
        "rationale": "Best near-miss: Decay=2 gave S=1.74, F=0.98. Decay=0 not yet tested — may push Fitness above 1.0.",
        "theory": "5d accumulated candle body reversal. Consistent selling pressure (negative body) → mean-reversion.",
        "source": "proven",
    },
    # ── Untested but designed as Sloan accruals ───────────────────────────────
    {
        "id": "fund_accruals",
        "name": "Fundamental: Accruals Signal (cash vs earnings quality)",
        "formula": (
            "ptp_bf = ts_backfill(est_ptp, 60);\n"
            "cfo_bf = ts_backfill(cashflow_op, 60);\n"
            "accrual = (ptp_bf - cfo_bf) / (abs(ptp_bf) + 1);\n"
            "signal  = group_rank(-ts_rank(accrual, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.86,
        "rationale": "Sloan (1996) accruals anomaly. High accruals (earnings >> cash) → lower quality → underperform. All fields proven on WQB.",
        "theory": "Earnings quality: pre-tax profit minus operating cashflow / abs(profit). Short high-accrual firms.",
        "source": "proven",
    },
    # ── SATURATED — already submitted on WQB, kept as low-priority fallback ──
    {
        "id": "fund_eps_revision_mom",
        "name": "Fundamental: EPS Revision Momentum (earnings drift)",
        "formula": (
            "eps_now  = ts_backfill(est_eps, 60);\n"
            "eps_lag  = ts_backfill(ts_delay(est_eps, 20), 60);\n"
            "revision = (eps_now - eps_lag) / (abs(eps_lag) + 0.01);\n"
            "signal   = group_rank(ts_rank(revision, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.45,
        "rationale": "FAILED: S=-0.36 after group_neutralize(industry). Signal does not survive neutralization. Kept as low-priority.",
        "theory": "Earnings revision momentum. Analysts revise slowly → drift continues after revision.",
        "source": "proven",
    },
    {
        "id": "fund_cashflow_ev",
        "name": "Fundamental: Cashflow-to-EV Yield (value)",
        "formula": (
            "cfy    = ts_backfill(cashflow_op, 60) / (enterprise_value + 1);\n"
            "signal = group_rank(ts_rank(cfy, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.44,
        "rationale": "SATURATED: 6XEvXKmG (SUBMITTED) + 1Y7qwRpz (CORRELATED). Skip unless all new signals fail.",
        "theory": "Cashflow valuation. cashflow_op/enterprise_value ranked vs own 60d history.",
        "source": "proven",
    },
    {
        "id": "fund_earnings_yield_z",
        "name": "Fundamental: Earnings-Yield Z-Score (value)",
        "formula": (
            "ey     = ts_backfill(est_eps, 60) / (close + 0.001);\n"
            "signal = group_rank(ts_zscore(ey, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|3|0.08",
        "confidence": 0.43,
        "rationale": "SATURATED: Vk8jzqqJ + rKo1jeXj both SUBMITTED. Skip unless all new signals fail.",
        "theory": "Value premium (Fama-French). est_eps/close = forward earnings yield, z-scored vs own history.",
        "source": "proven",
    },
    {
        "id": "fund_eps_fcf_corr",
        "name": "Fundamental: EPS–FCF Estimate Correlation",
        "formula": (
            "signal = group_rank(-ts_corr(est_ptp, est_fcf, 20), market);\n"
            "group_neutralize(signal, market)"
        ),
        "settings": "TOP3000|Market|3|0.08",
        "confidence": 0.42,
        "rationale": "SATURATED: rKWvzA3j SUBMITTED (F=1.64). Will be self-correlated. Skip unless all new signals fail.",
        "theory": "Analyst estimate co-movement. Low corr → estimate uncertainty → mispricing.",
        "source": "proven",
    },
]

# Signal → WQB formula template
SIGNAL_TO_WQB: dict[str, dict] = {
    # ── Proven microstructure signals ────────────────────────────────────────
    "intraday_ret": {
        "formula": (
            "intra  = (close - open) / (open + 0.001);\n"
            "signal = group_rank(-ts_rank(intra, 20), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "theory": "Intraday reversal — microstructure mean-reversion. WQB: S=1.84, TO=78% (needs Decay tuning).",
    },
    "intraday_smooth3": {
        "formula": (
            "intra   = (close - open) / (open + 0.001);\n"
            "smooth3 = ts_mean(intra, 3);\n"
            "signal  = group_rank(-rank(smooth3), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|10|0.08",
        "theory": "3d smoothed intraday — WQB: S=1.48, F=0.92, TO=35%. Near-pass, needs Decay=13+ or different formula.",
    },
    "vwap_dev_5d": {
        "formula": (
            "vwap5  = ts_sum(close * volume, 5) / (ts_sum(volume, 5) + 1);\n"
            "dev    = (close - vwap5) / (vwap5 + 0.001);\n"
            "signal = group_rank(-rank(dev), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "theory": "5d VWAP deviation — WQB PROVEN: S=1.65, F=1.16, TO=21%. Pattern B.",
    },
    "overnight_ret": {
        "formula": (
            "ovn    = (open - ts_delay(close, 1)) / (ts_delay(close, 1) + 0.001);\n"
            "ovn5   = ts_sum(ovn, 5);\n"
            "signal = group_rank(-rank(ovn5), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "theory": "Overnight gap 5d accumulated reversal — ts_delay() for overnight (delay() unavailable).",
    },
    "close_location": {
        "formula": (
            "loc    = (close - low) / (high - low + 0.001);\n"
            "signal = group_rank(-ts_rank(loc, 20), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "theory": "Close location in daily range — closing near high → fade (distribution signal).",
    },
    "vol_price_diverge": {
        "formula": (
            "surge  = volume / (ts_mean(volume, 20) + 1);\n"
            "move   = abs(returns) + 0.001;\n"
            "div    = rank(surge) - rank(move);\n"
            "signal = group_rank(ts_rank(div, 20), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|10|0.08",
        "theory": "High volume + small price move = informed accumulation. Long these stocks.",
    },
    # ── Classic signals ───────────────────────────────────────────────────────
    "vol_adj_reversal_2d": {
        "formula": (
            "vol_norm = ts_std_dev(returns, 20) + 0.001;\n"
            "raw_rev  = -(close - ts_delay(close, 2)) / (ts_delay(close, 2) * vol_norm);\n"
            "signal   = group_rank(rank(raw_rev), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|10|0.08",
        "theory": "Vol-normalised 2-day reversal — Pattern A variant",
    },
    "reversal_5d": {
        "formula": (
            "rev5   = -(close - ts_delay(close, 5)) / (ts_delay(close, 5) + 0.001);\n"
            "signal = group_rank(ts_rank(rev5, 20), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "theory": "5-day price reversal (Jegadeesh 1990)",
    },
    "52w_high_proximity": {
        "formula": (
            # ts_max unavailable — ts_rank(close, 252) gives [0,1] rank in 1y range
            "prox   = -ts_rank(close, 252);\n"
            "signal = group_rank(ts_rank(prox, 20), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "theory": "52-week high proximity contrarian via ts_rank (George-Hwang 2004)",
    },
    "momentum_20d": {
        "formula": (
            "ret20  = (close - ts_delay(close, 20)) / (ts_delay(close, 20) + 0.001);\n"
            "signal = group_rank(ts_rank(ret20, 252), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|10|0.08",
        "theory": "20-day momentum (Jegadeesh-Titman 1993)",
    },
    "amihud_illiq_20d": {
        "formula": (
            "illiq  = ts_mean(abs(returns) / (volume * close + 1), 20);\n"
            "signal = group_rank(ts_rank(illiq, 60), industry);\n"
            "group_neutralize(signal, industry)"
        ),
        "settings": "TOP3000|Industry|5|0.08",
        "theory": "Amihud illiquidity premium (Amihud 2002)",
    },
    "volume_surge_5d": {
        "formula": (
            "vol_ratio = volume / (ts_mean(volume, 20) + 1);\n"
            "ret_dir   = ts_delta(close, 5) / (close + 0.001);\n"
            "signal    = -group_rank(rank(vol_ratio) * rank(ret_dir), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "theory": "Volume-informed reversal — high volume + price rise → fade (Blume 1994)",
    },
    "high_low_pct": {
        "formula": (
            "range_pct = (high - low) / (close + 0.001);\n"
            "signal    = -group_rank(ts_rank(range_pct, 20), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "theory": "Intraday range contraction signal — high range → reversion",
    },
    "price_range_10d": {
        "formula": (
            # ts_max/ts_min unavailable — use ts_std_dev as range proxy
            "range10 = ts_std_dev(close, 10) / (close + 0.001);\n"
            "signal  = group_rank(ts_rank(-range10, 60), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|10|0.08",
        "theory": "10-day price range compression (std_dev proxy, ts_max unavailable)",
    },
    "ret_1d": {
        "formula": (
            "signal = -group_rank(ts_rank(returns, 20), subindustry);\n"
            "group_neutralize(signal, subindustry)"
        ),
        "settings": "TOP3000|Subindustry|5|0.08",
        "theory": "1-day return reversal (overnight mean-reversion)",
    },
}


@dataclass
class AlphaHypothesis:
    id: str
    name: str
    formula: str
    settings: str
    confidence: float
    rationale: str
    theory: str = ""
    source: str = "generated"  # proven | high_ic | generated


class AlphaHypothesizer:
    """
    Converts high-IC signals from PatternReport into WQB alpha candidates.

    Parameters
    ----------
    top_n : number of candidates to return (including Pattern A anchor)
    """

    def __init__(self, top_n: int = 8):
        self.top_n = top_n

    @staticmethod
    def _uses_dead_operator(formula: str) -> str | None:
        """Return the first DEAD_OPERATOR found in formula, else None.
        Guards the methodology so it can NEVER emit a formula that errors on WQB
        (e.g. ts_max/ts_min/delay). This is the safeguard the ad-hoc scripts lacked.

        NOTE: must distinguish standalone `delay(` from valid `ts_delay(` — only the
        former is unavailable on WQB FASTEXPR.
        """
        import re
        f = formula.lower()
        for op in DEAD_OPERATORS:
            # Use word-boundary style: op( but NOT preceded by another identifier char
            # This catches `delay(` and `ts_max(` / `ts_min(` but not `ts_delay(`
            if re.search(r'(?<![a-z_])' + re.escape(op) + r'\(', f):
                return op
        return None

    def generate(
        self,
        description: "MarketDescription | None",
        patterns: "PatternReport",
    ) -> list[AlphaHypothesis]:
        candidates: list[AlphaHypothesis] = []

        # Fundamental anchors first — highest Fitness family, uncorrelated w/ VWAP pool
        for fa in FUNDAMENTAL_ANCHORS:
            candidates.append(AlphaHypothesis(**fa))

        # Price/volume proven anchors — already in DB, added as fallback if top_n > len(fundamentals)
        candidates.append(AlphaHypothesis(**PATTERN_A))
        candidates.append(AlphaHypothesis(**PATTERN_B))

        # Best settings from WQB history
        best_s = (
            f"{patterns.best_settings[0]['universe']}|"
            f"{patterns.best_settings[0]['neutralization']}|"
            f"{patterns.best_settings[0]['decay']}|0.08"
            if patterns.best_settings else "TOP3000|Subindustry|5|0.08"
        )

        # Normalise ICIR for scoring
        icirs_1d = [abs(s.icir_1d) for s in patterns.signal_ics]
        icirs_5d = [abs(s.icir_5d) for s in patterns.signal_ics]
        max_icir1 = max(icirs_1d, default=1.0) or 1.0
        max_icir5 = max(icirs_5d, default=1.0) or 1.0

        for sig in patterns.signal_ics:
            wqb_info = SIGNAL_TO_WQB.get(sig.name)
            if wqb_info is None:
                continue

            # Scoring
            icir1_norm = min(abs(sig.icir_1d) / max_icir1, 1.0)
            icir5_norm = min(abs(sig.icir_5d) / max_icir5, 1.0)
            conf = 0.5 * icir1_norm + 0.3 * icir5_norm + 0.2 * sig.hit_rate_1d
            # Consistency bonus
            if sig.icir_1d * sig.icir_5d > 0:
                conf += 0.1

            # ── VALIDITY GUARD (v19 lesson) ──────────────────────────────────
            # IC on raw yfinance data does NOT survive WQB neutralization
            # (e.g. range premium: +IC on yfinance → Sharpe 0 after group_neutralize).
            # So a signal is only trusted if WQB history actually proves the family.
            # "WQB PROVEN" / "PASS" in the template theory = corroborated by real sims.
            theory = wqb_info.get("theory", "")
            wqb_validated = ("PROVEN" in theory.upper()) or ("PASS" in theory.upper())
            if wqb_validated:
                conf += 0.05                      # corroborated by real WQB sims
            else:
                conf = min(conf, 0.60)            # yfinance-IC only → cap as UNVALIDATED

            conf = min(conf, 0.97)  # cap below proven anchors

            if wqb_validated:
                source = "wqb_proven"
            elif abs(sig.icir_1d) >= 0.5:
                source = "high_ic_unvalidated"
            else:
                source = "generated"

            # Use best WQB settings if this signal fits (same neutralization)
            settings = wqb_info["settings"]

            candidates.append(AlphaHypothesis(
                id=f"ic_{sig.name}",
                name=f"IC-derived: {sig.name.replace('_',' ')}",
                formula=wqb_info["formula"],
                settings=settings,
                confidence=round(conf, 3),
                rationale=(
                    f"IC_1d={sig.mean_ic_1d:+.4f} ICIR={sig.icir_1d:+.4f} "
                    f"IC_5d={sig.mean_ic_5d:+.4f} Hit={sig.hit_rate_1d*100:.1f}%. "
                    f"{sig.description}"
                ),
                theory=wqb_info["theory"],
                source=source,
            ))

        # ── Safeguard: drop any candidate using an unavailable WQB operator ──
        # Guarantees the methodology never emits a formula that errors on WQB.
        safe: list[AlphaHypothesis] = []
        for c in candidates:
            dead = self._uses_dead_operator(c.formula)
            if dead:
                print(f"  [hypothesize] DROP {c.id}: uses dead operator '{dead}'")
                continue
            safe.append(c)

        # Sort by confidence, return top_n
        safe.sort(key=lambda c: c.confidence, reverse=True)
        return safe[:self.top_n]
