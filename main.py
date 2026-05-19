from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import time

from config import load_config
from dashboard.theory_catalog import THEORY_CATALOG
from api_layer.monitor_api import create_app
from pipeline.alpha_pipeline import AlphaPipeline
from pipeline.brute_force_workflow import BruteForceAlphaWorkflow


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def run_pipeline(args: argparse.Namespace) -> dict:
    config = load_config()
    if args.dry_run:
        config.settings.setdefault("app", {})["dry_run"] = True
        config.env["WQ_DRY_RUN"] = "true"
    configure_logging(config.settings["app"].get("log_level", "INFO"))

    if args.bruteforce:
        workflow = BruteForceAlphaWorkflow(config)
        report = workflow.run(
            strategy_type=args.strategy_type,
            count=args.count,
            skip=args.bruteforce_skip,
            submit_enabled=args.submit_bruteforce and not args.no_submit,
        )
        print(json.dumps(report, indent=2))
        return report

    pipeline = AlphaPipeline(config)
    report = pipeline.run_once(
        strategy_type=args.strategy_type,
        count=args.count,
        submit_enabled=not args.no_submit,
    )
    print(json.dumps(report, indent=2))
    return report


def sync_theories(args: argparse.Namespace) -> dict:
    config = load_config()
    configure_logging(config.settings["app"].get("log_level", "INFO"))
    pipeline = AlphaPipeline(config)
    synced = pipeline.store.sync_theory_catalog(THEORY_CATALOG, source="dashboard_catalog", created_by="system")
    pipeline.knowledge_base.load_all()
    result = {"synced": synced, "status": "ok"}
    print(json.dumps(result, indent=2))
    return result


def add_theory_from_file(args: argparse.Namespace) -> dict:
    config = load_config()
    configure_logging(config.settings["app"].get("log_level", "INFO"))
    pipeline = AlphaPipeline(config)
    theory_path = Path(args.add_theory_file).expanduser().resolve()
    payload = json.loads(theory_path.read_text(encoding="utf-8"))
    required = [
        "id",
        "domain",
        "title",
        "sector_tags",
        "core_principle",
        "alpha_implication",
        "example_expression",
        "agent_reasoning",
    ]
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Missing required theory keys: {', '.join(missing)}")
    pipeline.add_or_update_theory(
        payload["id"],
        domain=payload["domain"],
        title=payload["title"],
        sector_tags=list(payload["sector_tags"]),
        core_principle=payload["core_principle"],
        alpha_implication=list(payload["alpha_implication"]),
        example_expression=payload["example_expression"],
        agent_reasoning=list(payload["agent_reasoning"]),
        source=str(payload.get("source", "cli_json")),
        created_by=str(payload.get("created_by", "cli")),
        status=str(payload.get("status", "active")),
    )
    result = {"status": "ok", "theory_id": payload["id"], "path": str(theory_path)}
    print(json.dumps(result, indent=2))
    return result


def schedule_pipeline(args: argparse.Namespace) -> None:
    import schedule

    config = load_config()
    if args.dry_run:
        config.settings.setdefault("app", {})["dry_run"] = True
        config.env["WQ_DRY_RUN"] = "true"
    configure_logging(config.settings["app"].get("log_level", "INFO"))
    pipeline = AlphaPipeline(config)
    research_time = config.settings["pipeline"]["schedule"]["research"]
    generation_time = config.settings["pipeline"]["schedule"]["generation"]
    summary_time = config.settings["pipeline"]["schedule"]["summary"]

    schedule.every().day.at(research_time).do(
        lambda: (pipeline.daily_researcher.refresh(), pipeline.knowledge_base.load_all())
    )
    schedule.every().day.at(generation_time).do(
        pipeline.run_once,
        strategy_type=args.strategy_type,
        count=args.count,
        submit_enabled=not args.no_submit,
    )
    schedule.every().day.at(summary_time).do(lambda: logging.info("Current summary: %s", pipeline.store.summarize()))

    logging.info("Scheduler started. Pipeline will run daily at %s.", generation_time)
    while True:
        schedule.run_pending()
        time.sleep(1)


def run_continuous(args: argparse.Namespace) -> None:
    """Run research + simulation loop 24/7 with short sleep between cycles."""
    import time

    config = load_config()
    if args.dry_run:
        config.settings.setdefault("app", {})["dry_run"] = True
        config.env["WQ_DRY_RUN"] = "true"
    configure_logging(config.settings["app"].get("log_level", "INFO"))
    pipeline = AlphaPipeline(config)
    interval_seconds = int(config.settings.get("pipeline", {}).get("continuous_interval_seconds", 10))

    logging.info("Continuous 24/7 mode started. Sleeping %s seconds between cycles.", interval_seconds)
    while True:
        try:
            logging.info("=== Continuous cycle started ===")
            pipeline.daily_researcher.refresh()
            pipeline.knowledge_base.load_all()
            pipeline.run_once(
                strategy_type=args.strategy_type or "momentum",
                count=args.count or 8,
                submit_enabled=not args.no_submit,
            )
            logging.info("=== Continuous cycle finished. Sleeping %s seconds ===", interval_seconds)
        except Exception as exc:
            logging.exception("Continuous cycle failed: %s", exc)
        time.sleep(interval_seconds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WorldQuant Alpha System scaffold")
    parser.add_argument("--run-once", action="store_true", help="Run the pipeline immediately.")
    parser.add_argument("--schedule", action="store_true", help="Run the daily scheduler.")
    parser.add_argument("--continuous", action="store_true", help="Run research + simulation 24/7 continuously.")
    parser.add_argument("--serve-ui", action="store_true", help="Serve the React monitor API and built frontend.")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode.")
    parser.add_argument("--no-submit", action="store_true", help="Disable submission step.")
    parser.add_argument("--strategy-type", default=None, help="Override strategy type.")
    parser.add_argument("--count", type=int, default=None, help="Override number of candidates.")
    parser.add_argument("--bruteforce", action="store_true", help="Run brute-force alpha workflow.")
    parser.add_argument("--bruteforce-skip", type=int, default=0, help="Skip the first N brute-force candidates.")
    parser.add_argument("--submit-bruteforce", action="store_true", help="Allow brute-force workflow to submit passing alphas.")
    parser.add_argument("--sync-theories", action="store_true", help="Sync built-in theory catalog into the database.")
    parser.add_argument("--add-theory-file", default=None, help="Path to a JSON file describing a theory entry to upsert.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the React monitor API.")
    parser.add_argument("--port", type=int, default=8001, help="Port for the React monitor API.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.sync_theories:
        sync_theories(args)
        return
    if args.add_theory_file:
        add_theory_from_file(args)
        return
    if args.serve_ui:
        import uvicorn

        uvicorn.run(create_app(), host=args.host, port=args.port)
        return
    if args.schedule:
        schedule_pipeline(args)
        return
    if args.continuous:
        run_continuous(args)
        return
    if args.run_once or not args.schedule:
        run_pipeline(args)


if __name__ == "__main__":
    main()
