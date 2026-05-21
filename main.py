from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import time
import uuid

from config import load_config
from dashboard.theory_catalog import THEORY_CATALOG
from api_layer.monitor_api import create_app
from pipeline.alpha_pipeline import AlphaPipeline
from pipeline.brute_force_workflow import BruteForceAlphaWorkflow
from runtime.queue_manager import QueueManager
from runtime.queue_worker import QueueWorker


ROOT = Path(__file__).resolve().parent
PIPELINE_FIFO_DIR = ROOT / "runtime" / "pipeline_fifo"
PIPELINE_FIFO_STALE_SECONDS = 60 * 60 * 3
PIPELINE_FIFO_POLL_SECONDS = 1.0


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    log_level = getattr(logging, level.upper(), logging.INFO)
    for logger_name, log_path in (
        ("orchestration.deerflow_bridge", ROOT / "logs" / "deerflow" / "bridge.log"),
    ):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        if any(isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == log_path for handler in logger.handlers):
            continue
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
        handler.setLevel(log_level)
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        logger.addHandler(handler)


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    process_query_limited_information = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def _cleanup_pipeline_fifo() -> None:
    now = time.time()
    lock_path = PIPELINE_FIFO_DIR / "active.lock"
    try:
        if lock_path.exists():
            age_seconds = now - lock_path.stat().st_mtime
            remove_lock = age_seconds > PIPELINE_FIFO_STALE_SECONDS
            try:
                payload = json.loads(lock_path.read_text(encoding="utf-8", errors="ignore") or "{}")
            except json.JSONDecodeError:
                payload = {}
            pid = payload.get("pid")
            if pid is not None:
                if not _process_exists(int(pid)):
                    remove_lock = True
                    logging.warning("Removing pipeline FIFO lock held by dead pid=%s.", pid)
            if remove_lock:
                logging.warning("Removing stale pipeline FIFO lock at %s.", lock_path)
                lock_path.unlink(missing_ok=True)
        for ticket in PIPELINE_FIFO_DIR.glob("*.ticket"):
            if now - ticket.stat().st_mtime > PIPELINE_FIFO_STALE_SECONDS:
                logging.warning("Removing stale pipeline FIFO ticket %s.", ticket.name)
                ticket.unlink(missing_ok=True)
    except OSError:
        logging.warning("Pipeline FIFO cleanup encountered a filesystem error.", exc_info=True)


def _is_pipeline_ticket_turn(ticket: Path) -> bool:
    tickets = sorted(PIPELINE_FIFO_DIR.glob("*.ticket"), key=lambda path: path.name)
    return not tickets or tickets[0].name == ticket.name


def _try_acquire_pipeline_lock(ticket: Path, label: str) -> bool:
    lock_path = PIPELINE_FIFO_DIR / "active.lock"
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    try:
        payload = {
            "ticket": ticket.name,
            "label": label,
            "pid": os.getpid(),
            "acquired_at": time.time(),
        }
        os.write(fd, json.dumps(payload).encode("utf-8"))
    finally:
        os.close(fd)
    return True


@contextmanager
def pipeline_fifo_slot(label: str):
    PIPELINE_FIFO_DIR.mkdir(parents=True, exist_ok=True)
    ticket = PIPELINE_FIFO_DIR / f"{time.time_ns():020d}_{os.getpid()}_{uuid.uuid4().hex}.ticket"
    ticket.write_text(label, encoding="utf-8")
    acquired = False
    logging.info("Queued pipeline FIFO ticket %s for %s.", ticket.name, label)
    try:
        while True:
            _cleanup_pipeline_fifo()
            if _is_pipeline_ticket_turn(ticket) and _try_acquire_pipeline_lock(ticket, label):
                acquired = True
                logging.info("Acquired pipeline FIFO slot for %s.", label)
                break
            time.sleep(PIPELINE_FIFO_POLL_SECONDS)
        ticket.unlink(missing_ok=True)
        yield
    finally:
        if not acquired:
            ticket.unlink(missing_ok=True)
        if acquired:
            try:
                (PIPELINE_FIFO_DIR / "active.lock").unlink(missing_ok=True)
                logging.info("Released pipeline FIFO slot for %s.", label)
            except OSError:
                logging.warning("Failed to release pipeline FIFO lock.", exc_info=True)


def run_pipeline(args: argparse.Namespace) -> dict:
    config = load_config()
    if args.dry_run:
        config.settings.setdefault("app", {})["dry_run"] = True
        config.env["WQ_DRY_RUN"] = "true"
    configure_logging(config.settings["app"].get("log_level", "INFO"))

    label = f"bruteforce:{args.strategy_type or 'default'}" if args.bruteforce else f"pipeline:{args.strategy_type or 'default'}"
    with pipeline_fifo_slot(label):
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

    # Existing scheduled tasks
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

    # New task: Create and stimulate alphas every 4 minutes
    schedule.every(4).minutes.do(
        pipeline.run_once,
        strategy_type=args.strategy_type or "momentum",
        count=args.count or 1,
        submit_enabled=not args.no_submit,
    )

    logging.info("Scheduler started. Pipeline will run daily at %s and every 4 minutes for alpha stimulation.", generation_time)
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
    interval_seconds = int(
        args.continuous_interval_seconds
        or config.settings.get("pipeline", {}).get("continuous_interval_seconds", 10)
    )

    logging.info("Continuous 24/7 mode started. Sleeping %s seconds between cycles.", interval_seconds)
    while True:
        try:
            logging.info("=== Continuous cycle started ===")
            with pipeline_fifo_slot(f"continuous:{args.strategy_type or 'momentum'}"):
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
    parser.add_argument("--continuous-interval-seconds", type=int, default=None, help="Override sleep seconds between continuous cycles.")
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
    
    # Queue management arguments
    parser.add_argument("--queue-worker", action="store_true", help="Run as queue worker (process jobs from queue).")
    parser.add_argument("--queue-add", action="store_true", help="Add a job to the queue instead of running immediately.")
    parser.add_argument("--queue-status", action="store_true", help="Show queue status.")
    parser.add_argument("--queue-cleanup", action="store_true", help="Cleanup old jobs from queue.")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Poll interval for queue worker (seconds).")
    
    return parser


def run_queue_worker(args: argparse.Namespace) -> None:
    """Chạy queue worker để xử lý jobs"""
    config = load_config()
    configure_logging(config.settings["app"].get("log_level", "INFO"))
    
    queue_dir = config.root / "runtime" / "job_queue"
    queue_manager = QueueManager(queue_dir)
    
    # Cleanup old jobs
    removed = queue_manager.cleanup_old_jobs(max_age_seconds=86400 * 7)
    if removed > 0:
        logging.info("Cleaned up %d old jobs", removed)
    
    # Create and run worker
    worker = QueueWorker(config, queue_manager)
    logging.info("Starting queue worker...")
    worker.run(poll_interval=args.poll_interval)


def add_job_to_queue(args: argparse.Namespace) -> dict:
    """Thêm job vào hàng đợi thay vì chạy ngay"""
    config = load_config()
    configure_logging(config.settings["app"].get("log_level", "INFO"))
    
    queue_dir = config.root / "runtime" / "job_queue"
    queue_manager = QueueManager(queue_dir)
    
    # Xác định job type
    if args.bruteforce:
        job_type = "bruteforce"
    elif args.continuous:
        job_type = "continuous"
    else:
        job_type = "pipeline"
    
    # Tạo job
    job = queue_manager.create_job(
        job_type=job_type,
        strategy_type=args.strategy_type or "momentum",
        count=args.count or 8,
        submit_enabled=not args.no_submit,
        dry_run=args.dry_run,
    )
    
    result = {
        "status": "queued",
        "job_id": job.job_id,
        "job_type": job.job_type,
        "strategy_type": job.strategy_type,
        "count": job.count,
    }
    
    print(json.dumps(result, indent=2))
    logging.info("Job %s added to queue", job.job_id)
    return result


def show_queue_status(args: argparse.Namespace) -> dict:
    """Hiển thị trạng thái hàng đợi"""
    config = load_config()
    configure_logging(config.settings["app"].get("log_level", "INFO"))
    
    queue_dir = config.root / "runtime" / "job_queue"
    queue_manager = QueueManager(queue_dir)
    
    status = queue_manager.get_queue_status()
    print(json.dumps(status, indent=2))
    return status


def cleanup_queue(args: argparse.Namespace) -> dict:
    """Cleanup old jobs"""
    config = load_config()
    configure_logging(config.settings["app"].get("log_level", "INFO"))
    
    queue_dir = config.root / "runtime" / "job_queue"
    queue_manager = QueueManager(queue_dir)
    
    removed = queue_manager.cleanup_old_jobs(max_age_seconds=86400 * 7)
    result = {"removed": removed, "status": "ok"}
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    
    # Queue management commands
    if args.queue_worker:
        run_queue_worker(args)
        return
    if args.queue_add:
        add_job_to_queue(args)
        return
    if args.queue_status:
        show_queue_status(args)
        return
    if args.queue_cleanup:
        cleanup_queue(args)
        return
    
    # Original commands
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
