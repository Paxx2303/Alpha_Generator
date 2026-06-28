"""
check_self_corr.py — Kiểm tra SELF_CORRELATION cho tất cả gold alphas.

WQB standard: SELF_CORRELATION < 0.7 mới được submit.
Nếu corr >= 0.7 → alpha bị block, không thể submit.

Usage:
    python check_self_corr.py              # check tất cả gold alphas
    python check_self_corr.py --id abc123  # check 1 alpha cụ thể
"""
import argparse
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "data/alpha_store.db"
CORR_THRESHOLD = 0.7


def load_gold_alphas(alpha_id: str | None = None) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if alpha_id:
        cur.execute(
            "SELECT id, name, sharpe, fitness, status FROM gold_alphas WHERE id = ?",
            (alpha_id,),
        )
    else:
        cur.execute(
            "SELECT id, name, sharpe, fitness, status FROM gold_alphas ORDER BY fitness DESC"
        )
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "sharpe": r[2], "fitness": r[3], "status": r[4]}
        for r in rows
    ]


def check_self_corr_live(bot, alpha_id: str, max_retries: int = 5) -> dict:
    """Query WQB API for SELF_CORRELATION check result. Retries on 429."""
    for attempt in range(max_retries):
        try:
            res = bot.session.get(
                f"{bot.base_url}/alphas/{alpha_id}", headers=bot.headers
            )
            if res.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"    [429] Rate limit — waiting {wait}s...", flush=True)
                time.sleep(wait)
                continue
            if res.status_code != 200:
                return {"corr": None, "result": "HTTP_ERR", "detail": f"HTTP {res.status_code}"}
            data = res.json()
            checks = data.get("is", {}).get("checks", [])
            for c in checks:
                if c.get("name") == "SELF_CORRELATION":
                    val = c.get("value")
                    result = c.get("result", "UNKNOWN")
                    return {
                        "corr": val,
                        "result": result,
                        "passes": result != "FAIL" and (val is None or val < CORR_THRESHOLD),
                        "detail": f"corr={val:.4f} [{result}]" if val is not None else f"[{result}]",
                    }
            return {"corr": None, "result": "NOT_FOUND", "passes": True, "detail": "No SC check"}
        except Exception as e:
            return {"corr": None, "result": "ERROR", "passes": None, "detail": str(e)}
    return {"corr": None, "result": "RATE_LIMIT", "passes": None, "detail": "Max retries hit"}


def main():
    parser = argparse.ArgumentParser(description="Check SELF_CORRELATION for gold alphas")
    parser.add_argument("--id", dest="alpha_id", default=None, help="Check specific alpha ID")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between API calls")
    parser.add_argument("--unsubmitted", action="store_true", help="Only check UNSUBMITTED alphas")
    args = parser.parse_args()

    alphas = load_gold_alphas(args.alpha_id)
    if not alphas:
        print("No gold alphas found.")
        return

    if args.unsubmitted:
        alphas = [a for a in alphas if (a["status"] or "").upper() == "UNSUBMITTED"]
        print(f"  Filtering to UNSUBMITTED only: {len(alphas)} alphas")

    from wqb_automation import WQBAutomation, load_config
    config = load_config()
    bot = WQBAutomation(config)
    bot.start()

    print(f"\n{'='*75}")
    print(f"  SELF-CORRELATION CHECK — {len(alphas)} gold alphas (threshold < {CORR_THRESHOLD})")
    print(f"{'='*75}")
    print(f"  {'ID':12s}  {'S':>5}  {'F':>5}  {'Corr':>7}  {'Result':10}  Name")
    print(f"  {'-'*12}  {'-'*5}  {'-'*5}  {'-'*7}  {'-'*10}  {'-'*30}")

    pass_count = 0
    fail_count = 0
    pending_count = 0
    results = []

    for alpha in alphas:
        info = check_self_corr_live(bot, alpha["id"])
        corr_str = f"{info['corr']:.4f}" if info["corr"] is not None else "  None"
        result = info["result"]

        if result == "PASS" or (info["corr"] is not None and info["corr"] < CORR_THRESHOLD):
            icon = "[OK] "
            pass_count += 1
        elif result == "FAIL" or (info["corr"] is not None and info["corr"] >= CORR_THRESHOLD):
            icon = "[!!] "
            fail_count += 1
        else:
            icon = "[??] "
            pending_count += 1

        name_short = (alpha["name"] or "")[:45]
        print(f"  {icon}{alpha['id']:12s}  {alpha['sharpe']:5.2f}  {alpha['fitness']:5.2f}  {corr_str:>7}  {result:10}  {name_short}")
        results.append({**alpha, **info})

        time.sleep(args.delay)

    bot.stop()

    print(f"\n{'='*75}")
    print(f"  SUMMARY: {pass_count} PASS  |  {fail_count} FAIL (corr>=0.7)  |  {pending_count} PENDING/UNKNOWN")

    if fail_count > 0:
        print(f"\n  [!!] FAIL list (cannot submit):")
        for r in results:
            if r.get("corr") is not None and r["corr"] >= CORR_THRESHOLD:
                print(f"       {r['id']}  corr={r['corr']:.4f}  {r.get('name','')[:50]}")

    print(f"{'='*75}\n")


if __name__ == "__main__":
    main()
