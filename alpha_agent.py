"""
Alpha Agent — Autonomous WQ Brain Alpha Researcher & Tester.

Full loop:
  1. Research docs -> extract patterns & trends
  2. Generate hypothesis (economic rationale)
  3. Write WQ Brain alpha formula
  4. Submit to WQB via automation
  5. Wait for simulation results
  6. Analyze results (Sharpe, Fitness, Turnover, yearly)
  7. If pass -> optimize settings
  8. If fail -> diagnose & fix, or try new hypothesis
  9. Loop until pass criteria met or all hypotheses exhausted

Usage:
    python alpha_agent.py                         # Run full auto loop
    python alpha_agent.py --quick                  # Quick test mode (dry-run)
    python alpha_agent.py --headless               # Run browser headless
    python alpha_agent.py --max-cycles 10          # Max iterations
"""

import json
import os
import re
import sys
import time
import argparse
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.stdout.reconfigure(line_buffering=True)

from wqb_automation import WQBAutomation, load_config


# ========== EMBEDDED KNOWLEDGE BASE ==========

THEMES = {
    "mean_reversion": {
        "name": "Mean Reversion",
        "rationale": "Prices pushed too far from fair value tend to snap back. Stocks that fell most recently are likely to rebound.",
        "when": "After days of abnormally large moves / high volatility",
        "data_fields": ["close", "returns"],
        "core_operators": ["ts_delta", "ts_mean", "rank"],
        "best_lookback": "5-20 days",
        "settings": {"universe": "TOP3000", "neutralization": "Market",         "decay": 0, "truncation": 0.05},
        "base_formula": "-rank(ts_delta(close, 5))",
    },
    "momentum": {
        "name": "Momentum",
        "rationale": "Strong upward/downward trends tend to persist in the short/medium term. Recent winners continue to win.",
        "when": "Trending markets with high volume",
        "data_fields": ["close", "returns"],
        "core_operators": ["ts_mean", "ts_delta", "rank", "ts_decay_linear"],
        "best_lookback": "20-60 days",
        "settings": {"universe": "TOP1000", "neutralization": "Subindustry",         "decay": 3, "truncation": 0.10},
        "base_formula": "rank(ts_mean(returns, 10))",
    },
    "volume_price": {
        "name": "Volume-Price",
        "rationale": "Abnormal trading volume reveals hidden information. Negative covariance between price and volume signals reversal.",
        "when": "Exploiting information from trading activity",
        "data_fields": ["close", "volume", "open", "vwap"],
        "core_operators": ["ts_covariance", "rank", "ts_sum", "sign", "ts_mean"],
        "best_lookback": "5-10 days",
        "settings": {"universe": "TOP3000", "neutralization": "Market",         "decay": 0, "truncation": 0.05},
        "base_formula": "-rank(ts_covariance(rank(close), rank(volume), 5))",
    },
    "vwap_deviation": {
        "name": "VWAP Deviation",
        "rationale": "Price deviating far from VWAP tends to revert back. VWAP represents fair institutional value.",
        "when": "Intraday patterns, short-term mean reversion",
        "data_fields": ["vwap", "close", "high", "low"],
        "core_operators": ["ts_std_dev", "rank", "ts_decay_linear", "ts_arg_max"],
        "best_lookback": "1-5 days",
        "settings": {"universe": "TOP500", "neutralization": "Market",         "decay": 0, "truncation": 0.01},
        "base_formula": "rank(vwap - close)",
    },
    "volatility": {
        "name": "Volatility",
        "rationale": "Low-volatility stocks outperform (low-vol anomaly). Abnormal volatility spikes tend to revert.",
        "when": "After calm or chaotic market periods",
        "data_fields": ["returns", "close", "high", "low"],
        "core_operators": ["ts_std_dev", "ts_mean", "rank"],
        "best_lookback": "5-20 days",
        "settings": {"universe": "TOP1000", "neutralization": "Subindustry", "decay": 5, "truncation": 0.10},
        "base_formula": "-rank(ts_std_dev(returns, 20))",
    },
    "high_low_midpoint": {
        "name": "High-Low Midpoint",
        "rationale": "Close price deviating from high-low midpoint reflects intraday strength/weakness that reverts.",
        "when": "Any market condition",
        "data_fields": ["high", "low", "close"],
        "core_operators": ["ts_mean", "rank"],
        "best_lookback": "1-5 days",
        "settings": {"universe": "TOP3000", "neutralization": "Market", "decay": "0", "truncation": "0.05"},
        "base_formula": "rank((high + low) / 2 - close)",
    },
    "liquidity": {
        "name": "Liquidity",
        "rationale": "Illiquid stocks have a premium. Abnormal volume relative to average signals informed trading.",
        "when": "Exploiting illiquidity premium or sudden liquidity changes",
        "data_fields": ["volume", "returns", "close", "dvol", "adv20"],
        "core_operators": ["ts_mean", "abs", "rank", "pasteurize", "ts_delta"],
        "best_lookback": "20 days",
        "settings": {"universe": "TOP3000", "neutralization": "Market",         "decay": 3, "truncation": 0.05},
        "base_formula": "rank(volume / adv20)",
    },
    "regime_based": {
        "name": "Regime-Based",
        "rationale": "Signals only work under specific market conditions (high vol, volume surge). Filtering by regime dramatically increases Sharpe.",
        "when": "When signal has too much noise; proven IQC top 1.3% strategy",
        "data_fields": ["returns", "close", "volume", "adv20"],
        "core_operators": ["trade_when", "ts_rank", "ts_std_dev", "group_vector_neut", "ts_delay"],
        "best_lookback": "10 days (regime), 252 days (vol regime)",
        "settings": {"universe": "TOP3000", "neutralization": "Subindustry", "decay": 3, "truncation": 0.05},
        "base_formula": None,
    },
    "fundamental_value": {
        "name": "Fundamental Value",
        "rationale": "Value investing principles: buy cheap, high quality companies based on fundamental metrics like P/E, P/B, ROE.",
        "when": "Longer-term signals, finding mispriced assets",
        "data_fields": ["pe", "pb", "roe", "sales", "ebitda"],
        "core_operators": ["ts_backfill", "rank", "ts_delta"],
        "best_lookback": "Quarterly data, so focus on cross-sectional rank",
        "settings": {"universe": "TOP500", "neutralization": "Subindustry", "decay": 10, "truncation": 0.10},
        "base_formula": "rank(-ts_backfill(pe))",
    },
}

SETTINGS_GRID = [
    {"round": 1, "name": "Signal check", "universe": "TOP3000", "neutralization": "Market", "decay": 0, "truncation": 0.05},
    {"round": 2, "name": "Reduce turnover", "universe": "TOP3000", "neutralization": "Market", "decay": 5, "truncation": 0.05},
    {"round": 3, "name": "Increase Sharpe", "universe": "TOP3000", "neutralization": "Subindustry", "decay": 0, "truncation": 0.05},
    {"round": 4, "name": "Optimize Fitness", "universe": "TOP1000", "neutralization": "Subindustry", "decay": 10, "truncation": 0.10},
    {"round": 5, "name": "Maximize Sharpe", "universe": "TOP500", "neutralization": "Subindustry", "decay": 0, "truncation": 0.10},
]

PASS_TARGETS = {
    "sharpe_min": 1.25,
    "fitness_min": 1.0,
    "turnover_min": 10,
    "turnover_max": 70,
    "drawdown_max": 25,
}

# Proven alpha templates from research
PROVEN_ALPHAS = {
    "iqc_top_1pct": {
        "name": "IQC Top 1.3% (Sharpe 1.94)",
        "formula": (
            "lookback = 10;\n"
            "mr   = -rank((close - ts_delay(close, 2)) / ts_delay(close, 2) / (ts_std_dev(returns, 20) + 0.001));\n"
            "when = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;\n"
            "b    = trade_when(when, mr, -1);\n"
            "group_vector_neut(b, ts_mean(returns, 120), subindustry)"
        ),
        "settings": {"universe": "TOP3000", "neutralization": "Subindustry", "decay": 0, "truncation": 0.05},
    },
    "vol_weighted_mr": {
        "name": "Vol-Weighted MR",
        "formula": (
            "lookback = 5;\n"
            "raw_ret  = ts_sum(returns * volume, lookback) / (ts_sum(volume, lookback) + 1);\n"
            "vol_std  = ts_std_dev(returns, 20);\n"
            "-rank(raw_ret / (vol_std + 0.001))"
        ),
        "settings": {"universe": "TOP3000", "neutralization": "Market", "decay": 0, "truncation": 0.05},
    },
    "alpha_13": {
        "name": "Alpha #13 (101 Formulaic)",
        "formula": "-rank(ts_covariance(rank(close), rank(volume), 5))",
        "settings": {"universe": "TOP3000", "neutralization": "Market", "decay": 0, "truncation": 0.05},
    },
}


# ========== DIAGNOSIS ENGINE ==========

def diagnose(metrics: dict) -> list:
    fixes = []
    if metrics.get("sharpe") is None:
        return [{"issue": "NO_RESULT", "fix": "Check formula syntax. Run basic: rank(close) first.", "priority": 1}]

    s = metrics["sharpe"]
    t = metrics.get("turnover", 0)
    f = metrics.get("fitness", 0)
    d = metrics.get("drawdown", 0)
    yearly = metrics.get("yearly", [])

    if s > 4.0:
        fixes.append({"issue": f"LOOK_AHEAD_BIAS (Sharpe {s:.2f})", "fix": "Sharpe > 4.0 is abnormally high. Check for look-ahead bias (e.g. using future data like ts_delay(x, 0)). Ensure settings Delay=1.", "priority": 1})
    elif s < -0.5:
        fixes.append({"issue": f"WRONG_SIGN (Sharpe {s:.2f})", "fix": "Flip sign: add/remove '-' at front", "priority": 1})
    elif s < 0:
        fixes.append({"issue": f"SLIGHTLY_NEGATIVE (Sharpe {s:.2f})", "fix": "Flip sign: add/remove '-' at front", "priority": 1})
    elif s < 0.5:
        fixes.append({"issue": f"WEAK_SIGNAL (Sharpe {s:.2f})", "fix": "Signal too weak. Options: 1) Change data field 2) Change lookback 3) Add rank() wrapper 4) Try different theme", "priority": 2})
    elif s < 1.0:
        fixes.append({"issue": f"MODERATE_SIGNAL (Sharpe {s:.2f})", "fix": "Borderline. Try: 1) Add volatility normalization 2) Change neutralization 3) Add regime filter", "priority": 3})
    elif s < PASS_TARGETS["sharpe_min"]:
        fixes.append({"issue": f"BELOW_TARGET (Sharpe {s:.2f})", "fix": f"Need >= {PASS_TARGETS['sharpe_min']}. Try Subindustry neutral, shorter decay, add volume filter.", "priority": 4})

    if t > PASS_TARGETS["turnover_max"]:
        fixes.append({"issue": f"HIGH_TURNOVER ({t:.1f}%)", "fix": f"Turnover > {PASS_TARGETS['turnover_max']}%. Increase Decay or use ts_decay_linear(signal, 5)", "priority": 2})
    elif t < PASS_TARGETS["turnover_min"] and t > 0:
        fixes.append({"issue": f"LOW_TURNOVER ({t:.1f}%)", "fix": f"Turnover < {PASS_TARGETS['turnover_min']}%. Reduce Decay to 0 or use shorter lookback", "priority": 3})

    if d > PASS_TARGETS["drawdown_max"]:
        fixes.append({"issue": f"HIGH_DRAWDOWN ({d:.1f}%)", "fix": f"Drawdown > {PASS_TARGETS['drawdown_max']}%. Add regime filter or reduce concentration (Truncation to 0.03)", "priority": 3})

    if yearly:
        neg_years = [y for y in yearly if y.get("sharpe", 0) < 0]
        if len(neg_years) >= 2:
            years_str = ", ".join([str(y["year"]) for y in neg_years])
            fixes.append({"issue": f"UNSTABLE ({len(neg_years)} negative years: {years_str})", "fix": "Stability issue. Add regime filter (trade_when with vol condition) or group_vector_neut to remove momentum bias", "priority": 1})

    if s >= PASS_TARGETS["sharpe_min"] and f < PASS_TARGETS["fitness_min"]:
        fixes.append({"issue": "LOW_FITNESS", "fix": f"Fitness {f:.2f} < {PASS_TARGETS['fitness_min']}. Optimize settings through grid.", "priority": 4})

    return fixes


def get_next_hypothesis(history: list, failed_themes: list) -> dict:
    available = [t for t in THEMES if t not in failed_themes]
    if not available:
        return None

    # If we have results history, pick theme most different from what failed
    if history:
        last_theme = history[-1].get("theme", "")
        preferred = [t for t in available if t != last_theme]
        if preferred:
            available = preferred

    theme_key = available[0]
    theme = THEMES[theme_key]

    # Generate formula variants
    variants = generate_variants(theme_key, theme, history)

    return {
        "theme": theme_key,
        "name": theme["name"],
        "rationale": theme["rationale"],
        "variants": variants,
        "settings": dict(theme["settings"]),
    }


def generate_variants(theme_key: str, theme: dict, history: list) -> list:
    variants = []

    if theme_key == "mean_reversion":
        variants = [
            {"description": "Basic 5-day price delta", "formula": "-rank(ts_delta(close, 5))"},
            {"description": "Return-based 5-day", "formula": "-rank(ts_mean(returns, 5))"},
            {"description": "Multi-lookback combo", "formula": "-rank(ts_mean(returns, 5) + ts_mean(returns, 10))"},
            {"description": "Vol-normalized MR", "formula": "-rank(ts_delta(close, 5) / (ts_std_dev(returns, 20) + 0.001))"},
            {"description": "Volume-filtered MR", "formula": "if_else(ts_rank(volume, 20) < 0.5, -rank(ts_delta(close, 5)), 0)"},
            {"description": "Vol-weighted MR (proven)", "formula": "-rank(ts_sum(returns * volume, 5) / (ts_sum(volume, 5) + 1) / (ts_std_dev(returns, 20) + 0.001))"},
            {"description": "Regime-filtered MR (IQC top)", "formula": "lookback = 10;\nmr = -rank((close - ts_delay(close, 2)) / ts_delay(close, 2) / (ts_std_dev(returns, 20) + 0.001));\nwhen = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;\ntrade_when(when, mr, -1)"},
        ]
    elif theme_key == "momentum":
        variants = [
            {"description": "5-day momentum", "formula": "rank(ts_mean(returns, 5))"},
            {"description": "20-day momentum", "formula": "rank(ts_delta(close, 20))"},
            {"description": "Momentum skip last week", "formula": "rank(ts_delta(ts_delay(close, 5), 15))"},
            {"description": "Rank-based momentum", "formula": "ts_mean(rank(returns), 10)"},
        ]
    elif theme_key == "volume_price":
        variants = [
            {"description": "Alpha #13 neg covar", "formula": "-rank(ts_covariance(rank(close), rank(volume), 5))"},
            {"description": "Volume surge + low price", "formula": "rank(ts_rank(volume, 20)) * -rank(ts_delta(close, 5))"},
            {"description": "Money flow", "formula": "rank(ts_sum(sign(close - open) * volume, 10))"},
        ]
    elif theme_key == "vwap_deviation":
        variants = [
            {"description": "Basic VWAP deviation", "formula": "rank(vwap - close)"},
            {"description": "Vol-normalized VWAP", "formula": "rank((vwap - close) / ts_std_dev(close, 20))"},
            {"description": "VWAP + volume confirmation", "formula": "rank((vwap - close) / close) * rank(ts_rank(volume, 20))"},
        ]
    elif theme_key == "volatility":
        variants = [
            {"description": "Low vol factor", "formula": "-rank(ts_std_dev(returns, 20))"},
            {"description": "Vol spike reversal", "formula": "-rank(ts_std_dev(returns, 5) / ts_std_dev(returns, 20))"},
            {"description": "Range-based vol", "formula": "rank(-ts_mean((high - low) / close, 10))"},
        ]
    elif theme_key == "high_low_midpoint":
        variants = [
            {"description": "Basic midpoint", "formula": "rank((high + low) / 2 - close)"},
            {"description": "5-day midpoint", "formula": "rank(ts_mean((high + low) / 2 - close, 5))"},
            {"description": "Range position", "formula": "rank((close - low) / (high - low + 0.001))"},
        ]
    elif theme_key == "liquidity":
        variants = [
            {"description": "Abnormal volume", "formula": "rank(volume / adv20)"},
            {"description": "Amihud illiquidity", "formula": "rank(pasteurize(ts_mean(abs(returns) / (dvol + 1), 20)))"},
            {"description": "Liquidity drop", "formula": "rank(-ts_delta(adv20, 5))"},
        ]
    elif theme_key == "regime_based":
        variants = [
            {"description": "IQC top 1.3% (copy)", "formula": PROVEN_ALPHAS["iqc_top_1pct"]["formula"]},
            {"description": "Vol + Vol surge regime", "formula": "lookback = 10;\nsignal = 0.6 * (-rank(ts_delta(close, 5) / (ts_std_dev(returns, 20) + 0.001))) + 0.4 * rank(volume / adv20);\nvol_regime = ts_rank(ts_std_dev(returns, 22), 252) > 0.55;\nvol_surge = ts_rank(volume / adv20, 5) > 0.7;\nwhen = vol_regime && vol_surge;\ntrade_when(when, signal, -1)"},
        ]
    elif theme_key == "fundamental_value":
        variants = [
            {"description": "Value: low P/E", "formula": "rank(-ts_backfill(pe))"},
            {"description": "Value: low P/B", "formula": "rank(-ts_backfill(pb))"},
            {"description": "Quality: high ROE", "formula": "rank(ts_backfill(roe))"},
            {"description": "Combined Value & Quality", "formula": "rank(-ts_backfill(pe)) + rank(ts_backfill(roe))"},
            {"description": "Sales growth momentum", "formula": "rank(ts_delta(ts_backfill(sales), 252))"},
        ]

    if not variants:
        variants = [{"description": f"Base {theme['name']}", "formula": theme.get("base_formula", "rank(close)")}]

    if history:
        used = set()
        for h in history:
            if h.get("theme") == theme_key:
                used.add(h.get("variant_index", -1))
        variants = [v for i, v in enumerate(variants) if i not in used]

    return variants


def select_best_variant(hypothesis: dict, history: list) -> Optional[dict]:
    variants = hypothesis["variants"]
    if not variants:
        return None

    if not history:
        return {**variants[0], "index": 0}

    # Pick variant most different from last failed formula
    last_formula = history[-1].get("formula", "")
    for i, v in enumerate(variants):
        if v["formula"] != last_formula:
            return {**v, "index": i}

    return {**variants[0], "index": 0} if variants else None


def convert_settings(settings: dict) -> str:
    return f"{settings['universe']}|{settings['neutralization']}|{settings['decay']}|{settings['truncation']}"


def run_settings_grid(formula: str, history_entry: dict, auto: WQBAutomation) -> list:
    results = []
    for grid in SETTINGS_GRID:
        print(f"\n  Grid Round {grid['round']}: {grid['name']}")
        print(f"  {grid['universe']} | {grid['neutralization']} | Decay {grid['decay']} | Truncation {grid['truncation']}")

        settings_str = convert_settings(grid)
        result = auto.submit_alpha(formula, settings_str)
        result["grid_round"] = grid
        results.append(result)

        s = result.get("sharpe", 0) or 0
        if s >= PASS_TARGETS["sharpe_min"]:
            print(f"  ✅ Sharpe {s:.2f} >= {PASS_TARGETS['sharpe_min']} — promising!")
        elif s > 0:
            print(f"  Sharpe {s:.2f} — need improvement")

    best = max(results, key=lambda r: r.get("sharpe", -999) or -999)
    history_entry["grid_results"] = results
    history_entry["best_setting"] = best.get("grid_round", {})
    return results


# ========== MAIN AGENT LOOP ==========

def run_agent_loop(config: dict, max_cycles: int = 20, dry_run: bool = False):
    history = []
    failed_themes = []
    cycle = 0
    best_overall = {"sharpe": 0, "formula": "", "settings": ""}

    auto = None
    if not dry_run:
        auto = WQBAutomation(config)
        auto.start()
        auto.login()

    try:
        while cycle < max_cycles:
            cycle += 1
            print(f"\n{'='*70}")
            print(f"  CYCLE {cycle}/{max_cycles}")
            print(f"{'='*70}")

            # Step 1: Generate hypothesis
            hypothesis = get_next_hypothesis(history, failed_themes)
            if hypothesis is None:
                print("[AGENT] No more hypotheses. Exiting.")
                break

            print(f"\n[AGENT] Theme: {hypothesis['name']}")
            print(f"[AGENT] Rationale: {hypothesis['rationale']}")
            print(f"[AGENT] Variants available: {len(hypothesis['variants'])}")

            # Step 2: Select variant
            variant = select_best_variant(hypothesis, history)
            if variant is None:
                failed_themes.append(hypothesis["theme"])
                continue

            formula = variant["formula"]
            print(f"\n[AGENT] Selected variant: {variant['description']}")
            print(f"[AGENT] Formula:\n{formula}")

            if dry_run:
                print("\n[AGENT] DRY RUN — would submit:")
                print(f"  Formula: {variant['description']}")
                print(f"  Settings: {hypothesis['settings']}")
                history.append({
                    "cycle": cycle,
                    "theme": hypothesis["theme"],
                    "variant_index": variant.get("index", 0),
                    "formula": formula,
                    "settings": hypothesis["settings"],
                    "dry_run": True,
                })
                continue

            # Step 3: Submit alpha
            entry = {
                "cycle": cycle,
                "theme": hypothesis["theme"],
                "variant_index": variant.get("index", 0),
                "formula": formula,
                "settings": dict(hypothesis["settings"]),
                "timestamp": str(datetime.now()),
            }

            settings_str = convert_settings(hypothesis["settings"])
            result = auto.submit_alpha(formula, settings_str)
            entry["result"] = result

            # Step 4: Analyze
            s = result.get("sharpe")
            if s is None:
                print(f"[AGENT] ❌ Alpha error: {result.get('error', 'unknown')}")
                history.append(entry)
                failed_themes.append(hypothesis["theme"])
                continue

            print(f"\n[AGENT] 📊 Results: Sharpe={s:.2f}, Fitness={result.get('fitness', 'N/A')}, Turnover={result.get('turnover', 'N/A')}%")

            # Step 5: Diagnose
            diagnoses = diagnose(result)
            if diagnoses:
                print(f"[AGENT] Diagnoses ({len(diagnoses)} issues):")
                for d in diagnoses:
                    print(f"  [{d['priority']}] {d['issue']}: {d['fix']}")

            # Step 6: Check pass criteria
            if s >= PASS_TARGETS["sharpe_min"]:
                print(f"\n[AGENT] ✅ Sharpe {s:.2f} >= {PASS_TARGETS['sharpe_min']}!")
                f = result.get("fitness", 0) or 0
                if f >= PASS_TARGETS["fitness_min"]:
                    print(f"[AGENT] ✅ Fitness {f:.2f} >= {PASS_TARGETS['fitness_min']} too!")
                    print(f"[AGENT] 🎉 ALPHA PASSES! Running settings grid to optimize...")
                    run_settings_grid(formula, entry, auto)

                    best_entry = max(
                        entry.get("grid_results", []) + [entry["result"]],
                        key=lambda r: r.get("sharpe", -999) or -999
                    )
                    best_s = best_entry.get("sharpe", 0) or 0
                    if best_s > best_overall["sharpe"]:
                        best_overall = {
                            "sharpe": best_s,
                            "formula": formula,
                            "settings": best_entry.get("grid_round", entry["settings"]),
                        }
                else:
                    print(f"[AGENT] Fitness {f:.2f} < {PASS_TARGETS['fitness_min']}. Running settings grid...")
                    run_settings_grid(formula, entry, auto)

                # Save this alpha to gold file
                _save_gold_alpha(entry, result)

                # Try next theme for diversity
                failed_themes.append(hypothesis["theme"])
            else:
                print(f"[AGENT] ❌ Sharpe {s:.2f} < {PASS_TARGETS['sharpe_min']}. Diagnosing...")

                # Fix based on diagnosis
                if s < 0:
                    # Flip sign and retry
                    flipped = _flip_sign(formula)
                    if flipped and flipped != formula:
                        print(f"[AGENT] Flipping sign and retrying...")
                        entry["fix_attempt"] = "flip_sign"
                        entry["fixed_formula"] = flipped

                        settings_str = convert_settings(hypothesis["settings"])
                        result2 = auto.submit_alpha(flipped, settings_str)
                        s2 = result2.get("sharpe", 0) or 0
                        entry["fixed_result"] = result2
                        print(f"[AGENT] After flip: Sharpe={s2:.2f}")

                        if s2 >= PASS_TARGETS["sharpe_min"]:
                            print(f"[AGENT] ✅ Flip worked! Sharpe {s2:.2f}")
                            best_overall = {"sharpe": s2, "formula": flipped, "settings": hypothesis["settings"]}
                            _save_gold_alpha(entry, result2)
                        else:
                            failed_themes.append(hypothesis["theme"])
                    else:
                        failed_themes.append(hypothesis["theme"])
                else:
                    failed_themes.append(hypothesis["theme"])

            history.append(entry)
            print(f"\n[AGENT] Best so far: Sharpe {best_overall['sharpe']:.2f}")

    finally:
        if auto:
            auto.stop()

    print(f"\n{'='*70}")
    print(f"  AGENT COMPLETE — {cycle} cycles")
    print(f"{'='*70}")
    if best_overall["sharpe"] > 0:
        print(f"  Best alpha: Sharpe {best_overall['sharpe']:.2f}")
        print(f"  Formula:\n{best_overall['formula']}")
        print(f"  Settings: {best_overall['settings']}")
    else:
        print("  No passing alpha found.")

    return history, best_overall


def _flip_sign(formula: str) -> str:
    lines = formula.strip().split("\n")
    last = lines[-1].strip()

    if last.startswith("-"):
        lines[-1] = last[1:]
    elif last.startswith("rank("):
        lines[-1] = f"-{last}"
    elif last.startswith("zscore("):
        lines[-1] = f"-{last}"
    elif last.startswith("if_else("):
        lines[-1] = f"-rank({last})"
    else:
        lines[-1] = f"-({last})"

    return "\n".join(lines)


def _save_gold_alpha(entry: dict, result: dict):
    gold_dir = Path("wqb_logs")
    gold_dir.mkdir(exist_ok=True)
    path = gold_dir / "gold_alphas.json"

    gold = {
        "formula": entry["formula"],
        "settings": entry["settings"],
        "result": {k: result.get(k) for k in ["sharpe", "fitness", "turnover", "returns", "drawdown"]},
        "theme": entry["theme"],
        "timestamp": str(datetime.now()),
    }

    existing = []
    if path.exists():
        with open(path) as f:
            existing = json.load(f)

    existing.append(gold)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"[AGENT] 💎 Gold alpha saved to {path}")


def main():
    parser = argparse.ArgumentParser(description="Alpha Agent — Autonomous WQ Brain Alpha Researcher")
    parser.add_argument("--quick", action="store_true", help="Quick dry-run mode (no WQB)")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--max-cycles", type=int, default=20, help="Max iteration cycles")
    args = parser.parse_args()

    config = load_config()
    if args.headless:
        config["headless"] = True

    print("""
    ===========================================
          ALPHA AGENT v1.0
          Autonomous WQ Brain Alpha Researcher
    ===========================================
    """)
    print(f"  Mode: {'DRY RUN' if args.quick else 'LIVE'}")
    print(f"  Max cycles: {args.max_cycles}")
    print(f"  Themes available: {len(THEMES)}")
    print(f"  Proven alphas: {len(PROVEN_ALPHAS)}")
    print()

    history, best = run_agent_loop(
        config,
        max_cycles=args.max_cycles,
        dry_run=args.quick,
    )

    if args.quick:
        print("\n[AGENT] Dry-run complete. Remove --quick to run live.")
        print(f"[AGENT] Would test {len(history)} alphas across {len(set(h.get('theme') for h in history))} themes.")


if __name__ == "__main__":
    main()
