"""
Benchmark đối xứng: Alpha_Generator (Hermes + Theory RAG + Data Researcher)
vs worldquant-miner style (prompt thuần qua OpenRouter, không RAG, không review).

Cả hai cùng simulate thật qua `wq.simulate_expression()` để loại trừ khác biệt client.
In bảng chỉ số: Sharpe / Fitness / Turnover / Returns / Drawdown / SelfCorr.

Cách chạy:
    python -u benchmark_compare.py --n 2

Lưu ý: mỗi simulate thật trên WorldQuant Brain có thể mất nhiều phút.
Đặt N nhỏ (1-3) khi test nhanh; tăng dần khi muốn có trung bình ổn định.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import statistics
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logging.getLogger("api_layer.wq_client").setLevel(logging.INFO)
logging.getLogger("api_layer.session_manager").setLevel(logging.INFO)

from config import load_config
from api_layer import WQSessionManager, RateLimiter, WorldQuantClient
from pipeline.models import AlphaCandidate
from orchestration import HermesBridge
from orchestration.openai_fallback import OpenAIFallbackClient
from knowledge_base.alpha_theory_rag import get_theory_context_for_generation
from knowledge_base.data_researcher import DataResearcher


OPERATOR_CALL = re.compile(r"\b(?:rank|zscore|ts_mean|ts_delta|ts_std_dev|ts_corr|ts_rank)\s*\(")
FASTEXPR_LINE = re.compile(r"^[A-Za-z0-9_(),.+\-/*\s]+$")

ALPHA_META = {
    "delay": 1,
    "universe": "TOP3000",
    "truncation": 0.08,
    "region": "USA",
    "decay": 6,
    "neutralization": "SUBINDUSTRY",
    "pasteurization": "ON",
    "nanHandling": "OFF",
}


def parse_expressions(raw: str, limit: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("```"):
            continue
        line = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip().strip("`").strip()
        if not FASTEXPR_LINE.fullmatch(line):
            continue
        if not OPERATOR_CALL.search(line):
            continue
        if ":" in line or "—" in line or "–" in line:
            continue
        if line.count("(") != line.count(")"):
            continue
        canon = re.sub(r"\s+", "", line)
        if canon in seen:
            continue
        seen.add(canon)
        out.append(line)
        if len(out) >= limit:
            break
    return out


def build_alpha_generator_prompt(n: int, knowledge_root: Path, wq) -> str:
    theory = get_theory_context_for_generation(knowledge_root, "momentum")
    data_ctx = DataResearcher(knowledge_root, wq_client=wq).build_data_context("momentum")
    return (
        f"Generate {n} novel WorldQuant FASTEXPR momentum alphas.\n\n"
        "=== MANDATORY RULES ===\n"
        "- Use ONLY operators: ts_mean, ts_delta, ts_std_dev, ts_corr, rank, zscore, ts_rank\n"
        "- Lookbacks: 5, 10, 20, 60\n"
        "- Optimize for Fitness = Sharpe * sqrt(|returns| / max(turnover, 0.125))\n"
        "- Include at least one volume component\n"
        "- Output: exactly ONE clean expression per line. No markdown, no explanation.\n\n"
        f"=== THEORY GROUNDING ===\n{theory[:2000]}\n\n"
        f"=== DATA UNIVERSE ===\n{data_ctx[:1000]}\n\n"
        f"Now generate exactly {n} alphas, one per line:"
    )


def build_miner_prompt(n: int) -> str:
    # Prompt "thuần" kiểu worldquant-miner: chỉ yêu cầu sinh biểu thức, không RAG/không gate.
    return (
        f"Generate {n} WorldQuant FASTEXPR momentum alpha expressions. "
        "Return only the expressions, one per line, no explanation, no markdown."
    )


def simulate_all(wq, expressions: list[str], source: str) -> list[dict]:
    results = []
    for i, expr in enumerate(expressions, 1):
        print(f"  [{source} {i}/{len(expressions)}] {expr}")
        cand = AlphaCandidate(
            expression=expr, source=source, strategy_type="momentum", metadata=dict(ALPHA_META)
        )
        t0 = time.time()
        try:
            m = wq.simulate_expression(cand)
            dt = time.time() - t0
            row = {
                "expr": expr,
                "sharpe": m.sharpe,
                "fitness": m.fitness,
                "turnover": m.turnover,
                "returns": m.annual_returns,
                "drawdown": m.drawdown,
                "self_corr": m.self_correlation,
                "elapsed_s": round(dt, 1),
                "error": None,
            }
            print(
                f"    -> Sharpe={m.sharpe:.3f} Fitness={m.fitness:.3f} "
                f"Turnover={m.turnover:.3f} Returns={m.annual_returns:.4f} "
                f"DD={m.drawdown:.4f} SelfCorr={m.self_correlation:.4f} ({dt:.0f}s)"
            )
        except Exception as exc:
            dt = time.time() - t0
            row = {"expr": expr, "error": str(exc), "elapsed_s": round(dt, 1)}
            print(f"    -> ERROR ({dt:.0f}s): {exc}")
        results.append(row)
        time.sleep(2)
    return results


def aggregate(rows: list[dict]) -> dict:
    metric_keys = ["sharpe", "fitness", "turnover", "returns", "drawdown", "self_corr"]
    ok = [r for r in rows if r.get("error") is None]
    agg = {"n_total": len(rows), "n_ok": len(ok)}
    for k in metric_keys:
        vals = [r[k] for r in ok if isinstance(r.get(k), (int, float))]
        if vals:
            agg[f"{k}_mean"] = round(statistics.fmean(vals), 4)
            agg[f"{k}_median"] = round(statistics.median(vals), 4)
        else:
            agg[f"{k}_mean"] = None
            agg[f"{k}_median"] = None
    return agg


def print_table(name_a: str, agg_a: dict, name_b: str, agg_b: dict) -> None:
    keys = [
        ("n_ok", "Alpha hợp lệ"),
        ("sharpe_mean", "Sharpe (mean)"),
        ("sharpe_median", "Sharpe (median)"),
        ("fitness_mean", "Fitness (mean)"),
        ("fitness_median", "Fitness (median)"),
        ("turnover_mean", "Turnover (mean)"),
        ("returns_mean", "Returns (mean)"),
        ("drawdown_mean", "Drawdown (mean)"),
        ("self_corr_mean", "SelfCorr (mean)"),
    ]
    w = 22
    print("\n" + "=" * 78)
    print(f"{'Chỉ số':<{w}}{name_a:<{w}}{name_b:<{w}}")
    print("-" * 78)
    for k, label in keys:
        va = agg_a.get(k)
        vb = agg_b.get(k)
        print(f"{label:<{w}}{str(va):<{w}}{str(vb):<{w}}")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=2, help="Số alpha mỗi phía (mặc định 2).")
    parser.add_argument("--out", type=str, default="benchmark_result.json")
    args = parser.parse_args()
    n = args.n

    config = load_config()
    config.settings["app"]["dry_run"] = False
    config.env["WQ_DRY_RUN"] = "false"

    fallback = OpenAIFallbackClient(
        api_key=config.env.get("OPENROUTER_API_KEY", ""),
        base_url=config.env.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        model=config.env.get("OPENROUTER_MODEL_NAME", "openrouter/owl-alpha"),
        enabled=True,
    )
    hermes = HermesBridge(command="hermes", enabled=True, fallback_client=fallback)

    session = WQSessionManager(
        username=config.env.get("WQ_USERNAME", ""),
        password=config.env.get("WQ_PASSWORD", ""),
        base_url=config.settings["worldquant"]["base_url"],
        dry_run=False,
    )
    rate = RateLimiter(3)
    wq = WorldQuantClient(
        session_manager=session,
        rate_limiter=rate,
        base_url=config.settings["worldquant"]["base_url"],
        queue_dir=config.root / "runtime" / "simulation_fifo",
    )

    print("=" * 60)
    print(f"BENCHMARK: Alpha_Generator vs worldquant-miner (N={n} mỗi phía)")
    print("=" * 60)

    # ---------- Alpha_Generator (Hermes + RAG + Data Researcher) ----------
    print("\n[1/2] Sinh alpha kiểu Alpha_Generator (RAG + Data ctx)...")
    prompt_ag = build_alpha_generator_prompt(n, config.knowledge_root, wq)
    raw_ag = hermes.ask(prompt_ag)
    exprs_ag = parse_expressions(raw_ag, n)
    print(f"  -> Parsed {len(exprs_ag)} expressions: {exprs_ag}")
    if len(exprs_ag) < n:
        # Bổ sung fallback để N hai phía bằng nhau, đánh dấu rõ.
        fillers = [
            "rank(ts_delta(close, 20) / ts_std_dev(close, 20))",
            "rank(ts_corr(volume, returns, 5))",
            "-rank(close / ts_mean(close, 20))",
        ]
        for f in fillers:
            if len(exprs_ag) >= n:
                break
            if f not in exprs_ag:
                exprs_ag.append(f)
        print(f"  -> Bổ sung filler để đủ N={n}: {exprs_ag}")

    # ---------- worldquant-miner style (prompt thuần qua OpenRouter) ----------
    print("\n[2/2] Sinh alpha kiểu worldquant-miner (prompt thuần, không RAG)...")
    prompt_miner = build_miner_prompt(n)
    raw_miner = fallback.chat(prompt_miner) if fallback.available() else ""
    exprs_miner = parse_expressions(raw_miner, n)
    print(f"  -> Parsed {len(exprs_miner)} expressions: {exprs_miner}")
    if len(exprs_miner) < n:
        fillers = [
            "rank(ts_mean(returns, 20))",
            "rank(close / ts_mean(close, 20) - 1)",
            "rank(ts_delta(volume, 5) * -ts_delta(close, 5))",
        ]
        for f in fillers:
            if len(exprs_miner) >= n:
                break
            if f not in exprs_miner:
                exprs_miner.append(f)
        print(f"  -> Bổ sung filler để đủ N={n}: {exprs_miner}")

    # ---------- Simulate thật ----------
    print("\n--- SIMULATING Alpha_Generator side ---")
    rows_ag = simulate_all(wq, exprs_ag, "alpha_generator")
    print("\n--- SIMULATING worldquant-miner side ---")
    rows_miner = simulate_all(wq, exprs_miner, "worldquant_miner")

    agg_ag = aggregate(rows_ag)
    agg_miner = aggregate(rows_miner)
    print_table("Alpha_Generator", agg_ag, "worldquant-miner", agg_miner)

    out_path = Path(args.out)
    out_path.write_text(
        json.dumps(
            {
                "n_per_side": n,
                "alpha_generator": {"rows": rows_ag, "aggregate": agg_ag},
                "worldquant_miner": {"rows": rows_miner, "aggregate": agg_miner},
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nĐã lưu chi tiết vào: {out_path.resolve()}")


if __name__ == "__main__":
    main()
