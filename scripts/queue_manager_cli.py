#!/usr/bin/env python3
"""
CLI tool để quản lý hàng đợi alpha generation.

Usage:
    # Khởi động worker
    python scripts/queue_manager_cli.py start-worker
    
    # Thêm job vào hàng đợi
    python scripts/queue_manager_cli.py add-job --type pipeline --strategy momentum --count 5
    
    # Xem trạng thái hàng đợi
    python scripts/queue_manager_cli.py status
    
    # Cleanup old jobs
    python scripts/queue_manager_cli.py cleanup
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from runtime.queue_manager import QueueManager
from runtime.queue_worker import QueueWorker
import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def start_worker(args):
    """Khởi động queue worker"""
    setup_logging()
    config = load_config()
    queue_dir = config.root / "runtime" / "job_queue"
    queue_manager = QueueManager(queue_dir)
    
    # Cleanup old jobs
    removed = queue_manager.cleanup_old_jobs(max_age_seconds=86400 * 7)
    if removed > 0:
        print(f"Cleaned up {removed} old jobs")
    
    # Create and run worker
    worker = QueueWorker(config, queue_manager)
    print(f"Starting queue worker (poll_interval={args.poll_interval}s)...")
    print("Press Ctrl+C to stop")
    
    try:
        worker.run(poll_interval=args.poll_interval)
    except KeyboardInterrupt:
        print("\nWorker stopped by user")


def add_job(args):
    """Thêm job vào hàng đợi"""
    setup_logging()
    config = load_config()
    queue_dir = config.root / "runtime" / "job_queue"
    queue_manager = QueueManager(queue_dir)
    
    job = queue_manager.create_job(
        job_type=args.type,
        strategy_type=args.strategy,
        count=args.count,
        submit_enabled=not args.no_submit,
        dry_run=args.dry_run,
    )
    
    result = {
        "status": "queued",
        "job_id": job.job_id,
        "job_type": job.job_type,
        "strategy_type": job.strategy_type,
        "count": job.count,
        "submit_enabled": job.submit_enabled,
        "dry_run": job.dry_run,
    }
    
    print(json.dumps(result, indent=2))


def show_status(args):
    """Hiển thị trạng thái hàng đợi"""
    setup_logging()
    config = load_config()
    queue_dir = config.root / "runtime" / "job_queue"
    queue_manager = QueueManager(queue_dir)
    
    status = queue_manager.get_queue_status()
    
    print("\n=== QUEUE STATUS ===\n")
    
    # Active job
    if status["active_job"]:
        job = status["active_job"]
        print(f"🔄 ACTIVE JOB:")
        print(f"   Job ID: {job['job_id']}")
        print(f"   Type: {job['job_type']}")
        print(f"   Strategy: {job['strategy_type']}")
        print(f"   Count: {job['count']}")
        print(f"   Stage: {job.get('current_stage', 'N/A')}")
        
        # Hiển thị alpha đang xử lý
        if job.get('current_alpha_id'):
            print(f"   Current Alpha ID: {job['current_alpha_id']}")
        if job.get('current_alpha_expression'):
            expr = job['current_alpha_expression']
            print(f"   Current Expression: {expr[:60]}{'...' if len(expr) > 60 else ''}")
        
        # Hiển thị progress
        if job.get('progress'):
            prog = job['progress']
            print(f"   Progress: tested={prog.get('tested', 0)}, approved={prog.get('approved', 0)}")
        
        # Hiển thị alphas đã xử lý
        alphas_processed = job.get('alphas_processed', [])
        if alphas_processed:
            print(f"   Alphas Processed: {len(alphas_processed)}")
            # Hiển thị 3 alpha gần nhất
            for alpha in alphas_processed[-3:]:
                status_icon = "✅" if alpha['status'] in ('approved', 'submitted') else "❌"
                expr = alpha['expression'][:40]
                print(f"      {status_icon} {alpha['alpha_id']}: {expr}... ({alpha['status']})")
        
        # Hiển thị thống kê
        alphas_approved = job.get('alphas_approved', [])
        alphas_submitted = job.get('alphas_submitted', [])
        if alphas_approved or alphas_submitted:
            print(f"   Stats: approved={len(alphas_approved)}, submitted={len(alphas_submitted)}")
    else:
        print("🔄 ACTIVE JOB: None")
    
    print(f"\n📋 QUEUED: {status['queued_count']} jobs")
    for job in status["queued_jobs"]:
        print(f"   - {job['job_id']}: {job['job_type']} {job['strategy_type']} (count={job['count']})")
    
    print(f"\n⏸️  PAUSED: {status['paused_count']} jobs")
    for job in status["paused_jobs"]:
        print(f"   - {job['job_id']}: {job['job_type']} {job['strategy_type']}")
    
    print(f"\n✅ COMPLETED: {status['completed_count']} jobs")
    for job in status.get("recent_completed", [])[:3]:
        alphas_approved = len(job.get('alphas_approved', []))
        alphas_submitted = len(job.get('alphas_submitted', []))
        print(f"   - {job['job_id']}: {job['job_type']} {job['strategy_type']} (approved={alphas_approved}, submitted={alphas_submitted})")
    
    print(f"\n❌ FAILED: {status['failed_count']} jobs")
    for job in status.get("recent_failed", [])[:3]:
        error = job.get('error', 'Unknown error')[:60]
        print(f"   - {job['job_id']}: {job['job_type']} {job['strategy_type']} - {error}")
    
    print()


def cleanup(args):
    """Cleanup old jobs"""
    setup_logging()
    config = load_config()
    queue_dir = config.root / "runtime" / "job_queue"
    queue_manager = QueueManager(queue_dir)
    
    removed = queue_manager.cleanup_old_jobs(max_age_seconds=args.max_age)
    print(f"Cleaned up {removed} old jobs (max_age={args.max_age}s)")


def main():
    parser = argparse.ArgumentParser(description="Queue Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # start-worker command
    worker_parser = subparsers.add_parser("start-worker", help="Start queue worker")
    worker_parser.add_argument("--poll-interval", type=float, default=5.0, help="Poll interval (seconds)")
    worker_parser.set_defaults(func=start_worker)
    
    # add-job command
    add_parser = subparsers.add_parser("add-job", help="Add job to queue")
    add_parser.add_argument("--type", choices=["pipeline", "bruteforce", "continuous", "studio"], 
                           default="pipeline", help="Job type")
    add_parser.add_argument("--strategy", default="momentum", help="Strategy type")
    add_parser.add_argument("--count", type=int, default=8, help="Number of candidates")
    add_parser.add_argument("--no-submit", action="store_true", help="Disable submission")
    add_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    add_parser.set_defaults(func=add_job)
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show queue status")
    status_parser.set_defaults(func=show_status)
    
    # cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup old jobs")
    cleanup_parser.add_argument("--max-age", type=int, default=86400 * 7, 
                               help="Max age for old jobs (seconds)")
    cleanup_parser.set_defaults(func=cleanup)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
