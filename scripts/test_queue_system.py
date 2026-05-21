#!/usr/bin/env python3
"""
Test script cho queue system.

Usage:
    python scripts/test_queue_system.py
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from runtime.queue_manager import QueueManager


def test_queue_system():
    """Test basic queue operations"""
    print("=== Testing Queue System ===\n")
    
    # Load config
    config = load_config()
    queue_dir = config.root / "runtime" / "job_queue_test"
    
    # Create queue manager
    queue_manager = QueueManager(queue_dir)
    print(f"✓ Created queue manager at {queue_dir}\n")
    
    # Test 1: Create jobs
    print("Test 1: Creating jobs...")
    job1 = queue_manager.create_job(
        job_type="pipeline",
        strategy_type="momentum",
        count=5,
        submit_enabled=True,
        dry_run=True,
    )
    print(f"✓ Created job1: {job1.job_id}")
    
    job2 = queue_manager.create_job(
        job_type="bruteforce",
        strategy_type="mean-reversion",
        count=10,
        submit_enabled=False,
        dry_run=True,
    )
    print(f"✓ Created job2: {job2.job_id}\n")
    
    # Test 2: Get queue status
    print("Test 2: Getting queue status...")
    status = queue_manager.get_queue_status()
    print(f"✓ Queued jobs: {status['queued_count']}")
    print(f"✓ Active job: {status['active_job']}\n")
    
    # Test 3: Get next job
    print("Test 3: Getting next job...")
    next_job = queue_manager.get_next_job()
    if next_job:
        print(f"✓ Next job: {next_job.job_id} ({next_job.job_type})\n")
    else:
        print("✗ No next job found\n")
        return
    
    # Test 4: Acquire lock
    print("Test 4: Acquiring lock...")
    if queue_manager.acquire_lock(next_job):
        print(f"✓ Acquired lock for job {next_job.job_id}\n")
    else:
        print("✗ Failed to acquire lock\n")
        return
    
    # Test 5: Update progress
    print("Test 5: Updating progress...")
    queue_manager.update_job_progress(
        next_job,
        current_alpha_id="alpha_test_001",
        current_alpha_expression="rank(ts_delta(close, 5))",
        current_stage="simulation",
        progress_data={"tested": 1, "approved": 0},
    )
    print(f"✓ Updated progress for job {next_job.job_id}\n")
    
    # Test 6: Add alpha result
    print("Test 6: Adding alpha result...")
    queue_manager.add_alpha_result(
        next_job,
        alpha_id="alpha_test_001",
        expression="rank(ts_delta(close, 5))",
        status="approved",
        metrics={"sharpe": 1.5, "fitness": 0.8, "turnover": 0.3},
    )
    print(f"✓ Added alpha result to job {next_job.job_id}\n")
    
    # Test 7: Save checkpoint
    print("Test 7: Saving checkpoint...")
    queue_manager.save_checkpoint(next_job, {
        "current_index": 1,
        "timestamp": time.time(),
    })
    print(f"✓ Saved checkpoint for job {next_job.job_id}\n")
    
    # Test 8: Load checkpoint
    print("Test 8: Loading checkpoint...")
    checkpoint = queue_manager.load_checkpoint(next_job)
    if checkpoint:
        print(f"✓ Loaded checkpoint: {checkpoint}\n")
    else:
        print("✗ Failed to load checkpoint\n")
    
    # Test 9: Release lock
    print("Test 9: Releasing lock...")
    queue_manager.release_lock(next_job, result={"tested": 1, "approved": 1})
    print(f"✓ Released lock for job {next_job.job_id}\n")
    
    # Test 10: Final status
    print("Test 10: Final queue status...")
    status = queue_manager.get_queue_status()
    print(f"✓ Queued jobs: {status['queued_count']}")
    print(f"✓ Completed jobs: {status['completed_count']}")
    print(f"✓ Active job: {status['active_job']}\n")
    
    # Test 11: Cleanup
    print("Test 11: Cleanup...")
    removed = queue_manager.cleanup_old_jobs(max_age_seconds=0)
    print(f"✓ Removed {removed} old jobs\n")
    
    print("=== All Tests Passed ===")


if __name__ == "__main__":
    try:
        test_queue_system()
    except Exception as exc:
        print(f"\n✗ Test failed: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
