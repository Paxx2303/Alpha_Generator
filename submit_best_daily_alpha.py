#!/usr/bin/env python3
"""
submit_best_daily_alpha.py
──────────────────────────
Chọn alpha tốt nhất trong gold_alphas.json chưa submit và gửi lên WQB exchange.

Usage:
    python submit_best_daily_alpha.py           # dry-run (mặc định an toàn)
    python submit_best_daily_alpha.py --submit  # submit thật
    python submit_best_daily_alpha.py --list    # chỉ liệt kê unsubmitted, không làm gì
    python submit_best_daily_alpha.py --id <alpha_id> --submit  # submit 1 alpha cụ thể
"""
import argparse
import json
import logging
import sys
from pathlib import Path

# Đảm bảo import từ root project
sys.path.insert(0, str(Path(__file__).parent))
from config import GOLD_ALPHAS_PATH
from wqb_automation import WQBAutomation, load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── IQC thresholds (phải pass mới được submit) ────────────────────────────────
IQC_SHARPE_MIN   = 1.25
IQC_FITNESS_MIN  = 1.0
IQC_TURNOVER_MIN = 0.10   # 10%  (stored as fraction in gold_alphas)
IQC_TURNOVER_MAX = 0.70   # 70%


def load_alphas() -> list:
    if not GOLD_ALPHAS_PATH.exists():
        logger.error(f"gold_alphas.json not found at {GOLD_ALPHAS_PATH}")
        return []
    with open(GOLD_ALPHAS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_alphas(alphas: list) -> None:
    with open(GOLD_ALPHAS_PATH, "w", encoding="utf-8") as f:
        json.dump(alphas, f, indent=2, ensure_ascii=False)


def iqc_score(alpha: dict) -> float:
    """
    Composite score để xếp hạng alpha khi có nhiều UNSUBMITTED.

    Công thức: Sharpe * Fitness * turnover_bonus * drawdown_penalty
    
    - turnover_bonus   : reward turnover gần 30% (ideal), phạt nếu quá cao/thấp
    - drawdown_penalty : phạt drawdown lớn
    """
    sharpe   = alpha.get("sharpe",   0.0)
    fitness  = alpha.get("fitness",  0.0)
    turnover = alpha.get("turnover", 0.0)   # fraction (0–1)
    drawdown = alpha.get("drawdown", 0.0)   # fraction (0–1)

    # Turnover bonus: ideal = 0.30, peak = 1.0, giảm nếu lệch
    ideal_to = 0.30
    to_ratio = turnover / ideal_to if turnover > 0 else 0
    import math
    turnover_bonus = math.exp(-0.5 * (math.log(max(to_ratio, 0.01)) ** 2))

    # Drawdown penalty: mỗi 10% drawdown giảm score 10%
    drawdown_penalty = max(0.0, 1.0 - drawdown)

    return sharpe * fitness * turnover_bonus * drawdown_penalty


def passes_iqc(alpha: dict) -> tuple[bool, str]:
    """Trả về (pass, reason)."""
    sharpe   = alpha.get("sharpe",   0.0)
    fitness  = alpha.get("fitness",  0.0)
    turnover = alpha.get("turnover", 0.0)

    if sharpe < IQC_SHARPE_MIN:
        return False, f"Sharpe {sharpe:.2f} < {IQC_SHARPE_MIN}"
    if fitness < IQC_FITNESS_MIN:
        return False, f"Fitness {fitness:.2f} < {IQC_FITNESS_MIN}"
    if not (IQC_TURNOVER_MIN <= turnover <= IQC_TURNOVER_MAX):
        return False, f"Turnover {turnover*100:.1f}% outside [10%, 70%]"
    return True, "OK"


def print_alpha_table(alphas: list, title: str = "UNSUBMITTED ALPHAS") -> None:
    print(f"\n{'─'*80}")
    print(f"  {title}")
    print(f"{'─'*80}")
    print(f"  {'#':<3}  {'Name':<30}  {'Sharpe':>6}  {'Fitness':>7}  {'Turnover':>9}  {'Score':>6}  ID")
    print(f"  {'─'*3}  {'─'*30}  {'─'*6}  {'─'*7}  {'─'*9}  {'─'*6}  {'─'*8}")
    for i, a in enumerate(alphas, 1):
        name     = (a.get("name") or "Unnamed")[:30]
        sharpe   = a.get("sharpe",   0.0)
        fitness  = a.get("fitness",  0.0)
        turnover = a.get("turnover", 0.0) * 100
        score    = iqc_score(a)
        alpha_id = a.get("id", "?")
        ok, reason = passes_iqc(a)
        flag = "✅" if ok else "⚠️ "
        print(f"  {i:<3}  {name:<30}  {sharpe:>6.2f}  {fitness:>7.2f}  {turnover:>8.1f}%  {score:>6.3f}  {alpha_id}  {flag}")
    print(f"{'─'*80}\n")


def do_submit(auto: WQBAutomation, alpha: dict, dry_run: bool) -> bool:
    """Submit alpha, return True on success."""
    alpha_id = alpha.get("id")
    name     = alpha.get("name", "Unnamed")

    if dry_run:
        logger.info(f"[DRY RUN] Would submit: '{name}' (ID: {alpha_id})")
        logger.info(f"[DRY RUN] Sharpe={alpha.get('sharpe')}  Fitness={alpha.get('fitness')}  Turnover={alpha.get('turnover')*100:.1f}%")
        logger.info("[DRY RUN] Pass --submit to actually submit.")
        return False

    logger.info(f"Submitting '{name}' (ID: {alpha_id}) to exchange…")
    res = auto.submit_saved_alpha(alpha_id)
    status = res.get("status", "UNKNOWN")

    if status == "SUCCESS":
        logger.info("✅  Submission SUCCESS — all checks passed.")
        return True

    if status == "FAIL_CHECKS":
        failures = res.get("failures", [])
        logger.error(f"❌  Submission FAILED checks ({len(failures)} failure(s)):")
        for chk in failures:
            logger.error(f"    • {chk.get('name', '?')}: {chk.get('result', '?')} — {chk.get('message', '')}")
        return False

    if status == "TIMEOUT":
        logger.error("❌  Submission check polling timed out.")
        return False

    logger.error(f"❌  Submission returned unexpected status: {status}")
    logger.error(f"    Raw response: {json.dumps(res, indent=2)}")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Submit best unsubmitted alpha from gold_alphas.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--submit", action="store_true",
                        help="Actually submit (default is dry-run)")
    parser.add_argument("--list",   action="store_true",
                        help="Only list unsubmitted alphas and exit")
    parser.add_argument("--id",     type=str, default=None,
                        help="Force submit a specific alpha by ID")
    parser.add_argument("--top",    type=int, default=1,
                        help="Submit top N alphas instead of just 1 (default: 1)")
    args = parser.parse_args()

    dry_run = not args.submit

    # ── Load ──────────────────────────────────────────────────────────────────
    alphas = load_alphas()
    if not alphas:
        return

    # ── Filter candidates ─────────────────────────────────────────────────────
    if args.id:
        candidates = [a for a in alphas if a.get("id") == args.id]
        if not candidates:
            logger.error(f"Alpha ID '{args.id}' not found in gold_alphas.json")
            sys.exit(1)
    else:
        candidates = [a for a in alphas if a.get("status") == "UNSUBMITTED"]

    if not candidates:
        logger.info("No UNSUBMITTED alphas found. Nothing to do.")
        return

    # ── Sort by composite score ───────────────────────────────────────────────
    candidates.sort(key=iqc_score, reverse=True)

    print_alpha_table(candidates, "UNSUBMITTED ALPHAS (sorted by composite score)")

    if args.list:
        logger.info("--list mode: exiting without submitting.")
        return

    # ── IQC pre-check ─────────────────────────────────────────────────────────
    to_submit = []
    skipped   = []
    for alpha in candidates[: args.top]:
        ok, reason = passes_iqc(alpha)
        if ok:
            to_submit.append(alpha)
        else:
            skipped.append((alpha, reason))

    for alpha, reason in skipped:
        logger.warning(f"Skipping '{alpha.get('name')}' — fails IQC pre-check: {reason}")

    if not to_submit:
        logger.error("No candidates pass IQC thresholds. Check your gold_alphas.")
        sys.exit(1)

    # ── Connect ───────────────────────────────────────────────────────────────
    config = load_config()
    auto   = WQBAutomation(config)
    auto.start()

    if not auto.login():
        logger.error("Login failed — cannot submit.")
        auto.stop()
        sys.exit(1)

    # ── Submit loop ───────────────────────────────────────────────────────────
    submitted_count = 0
    for alpha in to_submit:
        success = do_submit(auto, alpha, dry_run)
        if success:
            # Update status in-memory
            for a in alphas:
                if a.get("id") == alpha.get("id"):
                    a["status"] = "SUBMITTED_SUCCESS"
            submitted_count += 1

    auto.stop()

    # ── Persist updated statuses ──────────────────────────────────────────────
    if submitted_count > 0:
        save_alphas(alphas)
        logger.info(f"Updated gold_alphas.json — {submitted_count} alpha(s) marked SUBMITTED_SUCCESS.")

    if dry_run:
        logger.info("This was a DRY RUN. Re-run with --submit to actually submit.")


if __name__ == "__main__":
    main()
