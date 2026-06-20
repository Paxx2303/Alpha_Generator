"""Alpha tools: simulate, diagnose, mutate, retrieve gold alphas."""
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_auto_instance = None
_is_logged_in  = False


def _get_automation():
    global _auto_instance, _is_logged_in
    import logging
    from wqb_automation import WQBAutomation, load_config
    if _auto_instance is None:
        config = load_config()
        config["headless"] = True
        _auto_instance = WQBAutomation(config)
        _auto_instance.start()
    if not _is_logged_in:
        _is_logged_in = _auto_instance.login()
        if not _is_logged_in:
            logging.error("WQB login failed")
    return _auto_instance


def _cleanup_automation():
    global _auto_instance
    if _auto_instance:
        _auto_instance.stop()


def submit_alpha(formula: str, settings: dict = None, dry_run: bool = False) -> str:
    """
    Submit an alpha formula to WorldQuant Brain for simulation.

    Args:
        formula:  WQB expression (e.g. "group_rank(-ts_corr(est_ptp, est_fcf, 20), market)")
        settings: dict with universe, neutralization, decay, truncation.
                  Defaults to TOP3000|Subindustry|3|0.08.
        dry_run:  If True, validate formula syntax only — no WQB call.

    Returns JSON string with sharpe, fitness, turnover, status.
    Pass criteria: Sharpe ≥ 1.25, Fitness ≥ 1.0, Turnover 10-70%.
    """
    if not settings:
        settings = {"universe": "TOP3000", "neutralization": "Subindustry", "decay": 3, "truncation": 0.08}

    settings_str = (
        f"{settings.get('universe','TOP3000')}|"
        f"{settings.get('neutralization','Subindustry')}|"
        f"{settings.get('decay',3)}|"
        f"{settings.get('truncation',0.08)}"
    )

    if dry_run:
        return json.dumps({"dry_run": True, "formula": formula, "settings": settings_str}, indent=2)

    try:
        auto = _get_automation()
        result = auto.submit_alpha(formula, settings_str)
        # Record result in DB
        try:
            from storage.store import Store
            s = Store()
            s.save_alpha_result({
                "formula": formula,
                "settings": settings_str,
                **result,
            })
            if _is_gold(result):
                s.upsert_gold_alpha({"formula": formula, "settings": settings_str, **result})
            s.close()
        except Exception:
            pass
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _is_gold(r: dict) -> bool:
    return (
        float(r.get("sharpe", 0)) >= 1.25
        and float(r.get("fitness", 0)) >= 1.0
        and 0.10 <= float(r.get("turnover", 0)) <= 0.70
    )


def get_gold_alphas() -> str:
    """
    Return all gold alphas from alpha_store.db (Sharpe ≥ 1.25, Fitness ≥ 1.0).
    Use as inspiration or mutation seeds. Avoid correlation > 0.7 with existing ones.
    """
    try:
        from storage.store import Store
        s = Store()
        alphas = s.get_gold_alphas()
        s.close()
        return json.dumps(alphas, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def diagnose_alpha(metrics: dict) -> dict:
    """
    Analyse alpha backtest metrics and return structured diagnosis + fix recommendations.

    Args:
        metrics: dict with keys sharpe, fitness, turnover, drawdown (all floats).

    Returns: {pass: bool, issues: [...], fixes: [...]}
    """
    sharpe   = float(metrics.get("sharpe", 0))
    fitness  = float(metrics.get("fitness", 0))
    turnover = float(metrics.get("turnover", 0))

    issues, fixes = [], []

    if sharpe < 1.25:
        issues.append(f"Sharpe {sharpe:.2f} < 1.25")
        fixes.append("Try group_neutralize(signal, subindustry) or increase lookback window.")

    if fitness < 1.0:
        issues.append(f"Fitness {fitness:.2f} < 1.0")
        fixes.append("Add truncate(signal, 0.08) to cap outliers. Fitness = Sharpe × √(|Returns|/max(TO,0.125)).")

    if turnover < 0.10:
        issues.append(f"Turnover {turnover*100:.1f}% < 10%")
        fixes.append("Reduce decay parameter (try decay=1 or decay=0).")

    if turnover > 0.70:
        issues.append(f"Turnover {turnover*100:.1f}% > 70%")
        fixes.append("Increase decay parameter (try decay=6 or decay=10).")

    return {
        "pass": len(issues) == 0,
        "issues": issues,
        "fixes": fixes,
    }


def mutate_formula(formula: str, n: int = 3) -> list:
    """
    Generate n variations of a formula using mutation strategies:
    1. Shorter lookback (×0.6)
    2. Longer lookback (×2)
    3. Replace 'close' with 'vwap'
    4. Volatility normalisation wrapper

    Returns list of formula strings.
    """
    mutations = []

    m = re.search(r",\s*(\d+)\s*\)", formula)
    if m:
        orig = int(m.group(1))
        short = max(1, round(orig * 0.6))
        long  = round(orig * 2)
        mutations.append(formula.replace(f", {orig})", f", {short})"))
        mutations.append(formula.replace(f", {orig})", f", {long})"))

    if "close" in formula:
        mutations.append(formula.replace("close", "vwap"))

    mutations.append(f"({formula}) / (ts_std_dev(returns, 20) + 0.001)")

    return mutations[:n]
