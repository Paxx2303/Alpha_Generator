"""
Queue Worker - Worker để xử lý các jobs trong hàng đợi.
Tự động chạy job tiếp theo khi job hiện tại hoàn thành.
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any

from config import AppConfig, load_config
from pipeline.alpha_pipeline import AlphaPipeline
from pipeline.brute_force_workflow import BruteForceAlphaWorkflow
from runtime.queue_manager import QueueJob, QueueManager
from runtime.tracked_pipeline import TrackedPipeline

LOGGER = logging.getLogger(__name__)


class QueueWorker:
    """
    Worker để xử lý các jobs trong hàng đợi.
    
    Features:
    - Tự động lấy job tiếp theo từ hàng đợi
    - Xử lý job (pipeline, bruteforce, continuous, studio)
    - Lưu checkpoint khi nhận signal SIGTERM/SIGINT
    - Resume job từ checkpoint khi khởi động lại
    - Tự động submit alpha khi hoàn thành
    """

    def __init__(self, config: AppConfig, queue_manager: QueueManager):
        self.config = config
        self.queue_manager = queue_manager
        self.current_job: QueueJob | None = None
        self.should_stop = False
        self.pipeline: AlphaPipeline | None = None
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Xử lý signal (SIGTERM, SIGINT) để lưu checkpoint"""
        LOGGER.info("Received signal %d, saving checkpoint...", signum)
        self.should_stop = True
        
        if self.current_job:
            # Lưu checkpoint
            checkpoint_data = {
                "signal": signum,
                "timestamp": time.time(),
                "job_id": self.current_job.job_id,
                "progress": self.current_job.progress or {},
            }
            self.queue_manager.save_checkpoint(self.current_job, checkpoint_data)
            LOGGER.info("Checkpoint saved for job %s", self.current_job.job_id)

    def run(self, poll_interval: float = 5.0) -> None:
        """
        Chạy worker loop.
        
        Args:
            poll_interval: Thời gian chờ giữa các lần poll (seconds)
        """
        LOGGER.info("Queue worker started (poll_interval=%.1fs)", poll_interval)
        
        while not self.should_stop:
            try:
                # Lấy job tiếp theo
                job = self.queue_manager.get_next_job()
                
                if not job:
                    # Không có job nào, chờ
                    LOGGER.debug("No jobs in queue, waiting...")
                    time.sleep(poll_interval)
                    continue
                
                # Cố gắng acquire lock
                if not self.queue_manager.acquire_lock(job):
                    LOGGER.debug("Failed to acquire lock, another worker is running")
                    time.sleep(poll_interval)
                    continue
                
                # Chạy job
                self.current_job = job
                LOGGER.info("Processing job %s: %s %s", job.job_id, job.job_type, job.strategy_type)
                
                try:
                    result = self._process_job(job)
                    self.queue_manager.release_lock(job, result=result)
                    LOGGER.info("Job %s completed successfully", job.job_id)
                    
                except Exception as exc:
                    LOGGER.error("Job %s failed: %s", job.job_id, exc, exc_info=True)
                    self.queue_manager.release_lock(job, error=str(exc))
                
                finally:
                    self.current_job = None
                
            except Exception as exc:
                LOGGER.error("Worker loop error: %s", exc, exc_info=True)
                time.sleep(poll_interval)
        
        LOGGER.info("Queue worker stopped")

    def _process_job(self, job: QueueJob) -> dict[str, Any]:
        """
        Xử lý một job.
        
        Returns:
            Kết quả của job (report)
        """
        # Kiểm tra xem có checkpoint không
        checkpoint = self.queue_manager.load_checkpoint(job)
        if checkpoint:
            LOGGER.info("Resuming job %s from checkpoint", job.job_id)
        
        # Cập nhật config
        if job.dry_run:
            self.config.settings.setdefault("app", {})["dry_run"] = True
            self.config.env["WQ_DRY_RUN"] = "true"
        
        # Xử lý theo loại job
        if job.job_type == "pipeline":
            return self._process_pipeline_job(job, checkpoint)
        elif job.job_type == "bruteforce":
            return self._process_bruteforce_job(job, checkpoint)
        elif job.job_type == "continuous":
            return self._process_continuous_job(job, checkpoint)
        elif job.job_type == "studio":
            return self._process_studio_job(job, checkpoint)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")

    def _process_pipeline_job(self, job: QueueJob, checkpoint: dict[str, Any] | None) -> dict[str, Any]:
        """Xử lý pipeline job"""
        pipeline = AlphaPipeline(self.config)
        self.pipeline = pipeline
        
        # Wrap pipeline với tracker
        tracked_pipeline = TrackedPipeline(pipeline, self.queue_manager, job)
        
        # Chạy pipeline
        report = tracked_pipeline.run_once(
            strategy_type=job.strategy_type,
            count=job.count,
            submit_enabled=job.submit_enabled,
        )
        
        return report

    def _process_bruteforce_job(self, job: QueueJob, checkpoint: dict[str, Any] | None) -> dict[str, Any]:
        """Xử lý bruteforce job"""
        workflow = BruteForceAlphaWorkflow(self.config)
        
        # Lấy skip từ checkpoint nếu có
        skip = 0
        if checkpoint and "skip" in checkpoint:
            skip = checkpoint["skip"]
            LOGGER.info("Resuming bruteforce from skip=%d", skip)
        
        report = workflow.run(
            strategy_type=job.strategy_type,
            count=job.count,
            skip=skip,
            submit_enabled=job.submit_enabled,
        )
        
        return report

    def _process_continuous_job(self, job: QueueJob, checkpoint: dict[str, Any] | None) -> dict[str, Any]:
        """Xử lý continuous job (chạy liên tục)"""
        pipeline = AlphaPipeline(self.config)
        self.pipeline = pipeline
        
        # Wrap pipeline với tracker
        tracked_pipeline = TrackedPipeline(pipeline, self.queue_manager, job)
        
        cycle_count = 0
        if checkpoint and "cycle_count" in checkpoint:
            cycle_count = checkpoint["cycle_count"]
        
        # Chạy một cycle
        pipeline.daily_researcher.refresh()
        pipeline.knowledge_base.load_all()
        
        report = tracked_pipeline.run_once(
            strategy_type=job.strategy_type,
            count=job.count,
            submit_enabled=job.submit_enabled,
        )
        
        cycle_count += 1
        
        # Lưu checkpoint cho cycle tiếp theo
        checkpoint_data = {
            "cycle_count": cycle_count,
            "last_cycle_at": time.time(),
        }
        self.queue_manager.save_checkpoint(job, checkpoint_data)
        
        # Đánh dấu job là "queued" để chạy lại
        job.status = "queued"
        self.queue_manager._save_job(job)
        
        return report

    def _process_studio_job(self, job: QueueJob, checkpoint: dict[str, Any] | None) -> dict[str, Any]:
        """Xử lý studio job"""
        # TODO: Implement studio job processing
        return {"status": "not_implemented"}


def main():
    """Main entry point cho queue worker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Queue Worker for Alpha Generation")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Poll interval in seconds")
    parser.add_argument("--cleanup-age", type=int, default=86400 * 7, help="Max age for old jobs (seconds)")
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    
    # Create queue manager
    queue_dir = config.root / "runtime" / "job_queue"
    queue_manager = QueueManager(queue_dir)
    
    # Cleanup old jobs
    removed = queue_manager.cleanup_old_jobs(max_age_seconds=args.cleanup_age)
    if removed > 0:
        LOGGER.info("Cleaned up %d old jobs", removed)
    
    # Create and run worker
    worker = QueueWorker(config, queue_manager)
    
    try:
        worker.run(poll_interval=args.poll_interval)
    except KeyboardInterrupt:
        LOGGER.info("Worker interrupted by user")
    except Exception as exc:
        LOGGER.error("Worker failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
