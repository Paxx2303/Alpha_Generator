"""
Queue Manager - Quản lý hàng đợi FIFO cho các chương trình alpha generation.
Chỉ cho phép 1 chương trình chạy tại một thời điểm.
Lưu trạng thái khi tắt và tiếp tục khi khởi động lại.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

LOGGER = logging.getLogger(__name__)


@dataclass
class QueueJob:
    """Đại diện cho một công việc trong hàng đợi"""
    job_id: str
    job_type: Literal["pipeline", "bruteforce", "continuous", "studio"]
    strategy_type: str
    count: int
    submit_enabled: bool
    dry_run: bool
    created_at: float
    started_at: float | None = None
    completed_at: float | None = None
    status: Literal["queued", "running", "paused", "completed", "failed"] = "queued"
    progress: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    checkpoint: dict[str, Any] | None = None
    pid: int | None = None
    # Alpha tracking
    current_alpha_id: str | None = None
    current_alpha_expression: str | None = None
    current_stage: str | None = None
    alphas_processed: list[dict[str, Any]] | None = None
    alphas_approved: list[str] | None = None
    alphas_submitted: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueueJob:
        return cls(**data)


class QueueManager:
    """
    Quản lý hàng đợi FIFO cho các chương trình alpha generation.
    
    Features:
    - Chỉ cho phép 1 job chạy tại một thời điểm
    - Lưu trạng thái khi tắt (checkpoint)
    - Tiếp tục chạy khi khởi động lại (resume)
    - Tự động submit alpha khi hoàn thành
    """

    def __init__(self, queue_dir: Path):
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.active_lock_path = self.queue_dir / "active.lock"
        self.jobs_dir = self.queue_dir / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir = self.queue_dir / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def create_job(
        self,
        job_type: Literal["pipeline", "bruteforce", "continuous", "studio"],
        strategy_type: str,
        count: int,
        submit_enabled: bool = True,
        dry_run: bool = False,
    ) -> QueueJob:
        """Tạo một job mới và thêm vào hàng đợi"""
        job_id = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        job = QueueJob(
            job_id=job_id,
            job_type=job_type,
            strategy_type=strategy_type,
            count=count,
            submit_enabled=submit_enabled,
            dry_run=dry_run,
            created_at=time.time(),
            status="queued",
        )
        self._save_job(job)
        LOGGER.info("Created job %s: %s %s (count=%d)", job_id, job_type, strategy_type, count)
        return job

    def get_next_job(self) -> QueueJob | None:
        """Lấy job tiếp theo trong hàng đợi (FIFO)"""
        # Kiểm tra xem có job nào đang chạy không
        active_job = self.get_active_job()
        if active_job:
            LOGGER.debug("Job %s is currently running", active_job.job_id)
            return None

        # Tìm job đầu tiên có status = "queued" hoặc "paused"
        jobs = self._list_jobs()
        for job in sorted(jobs, key=lambda j: j.created_at):
            if job.status in ("queued", "paused"):
                return job
        
        return None

    def acquire_lock(self, job: QueueJob) -> bool:
        """Cố gắng acquire lock để chạy job"""
        try:
            # Kiểm tra xem có lock nào đang tồn tại không
            if self.active_lock_path.exists():
                # Kiểm tra xem process còn sống không
                lock_data = self._read_lock()
                if lock_data and lock_data.get("pid"):
                    if self._process_exists(lock_data["pid"]):
                        LOGGER.debug("Lock is held by active process %d", lock_data["pid"])
                        return False
                    else:
                        LOGGER.warning("Removing stale lock from dead process %d", lock_data["pid"])
                        self.active_lock_path.unlink(missing_ok=True)

            # Tạo lock mới
            fd = os.open(self.active_lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                lock_data = {
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "strategy_type": job.strategy_type,
                    "pid": os.getpid(),
                    "acquired_at": time.time(),
                }
                os.write(fd, json.dumps(lock_data).encode("utf-8"))
            finally:
                os.close(fd)

            # Cập nhật job status
            job.status = "running"
            job.started_at = time.time()
            job.pid = os.getpid()
            self._save_job(job)
            
            LOGGER.info("Acquired lock for job %s", job.job_id)
            return True

        except FileExistsError:
            LOGGER.debug("Lock already exists")
            return False
        except Exception as exc:
            LOGGER.error("Failed to acquire lock: %s", exc, exc_info=True)
            return False

    def release_lock(self, job: QueueJob, result: dict[str, Any] | None = None, error: str | None = None) -> None:
        """Release lock sau khi job hoàn thành hoặc thất bại"""
        try:
            # Cập nhật job status
            if error:
                job.status = "failed"
                job.error = error
            else:
                job.status = "completed"
                job.result = result
            
            job.completed_at = time.time()
            self._save_job(job)

            # Xóa lock
            self.active_lock_path.unlink(missing_ok=True)
            LOGGER.info("Released lock for job %s (status=%s)", job.job_id, job.status)

        except Exception as exc:
            LOGGER.error("Failed to release lock: %s", exc, exc_info=True)

    def save_checkpoint(self, job: QueueJob, checkpoint_data: dict[str, Any]) -> None:
        """Lưu checkpoint cho job (để resume sau khi tắt)"""
        job.checkpoint = checkpoint_data
        job.status = "paused"
        self._save_job(job)
        
        # Lưu checkpoint riêng
        checkpoint_path = self.checkpoints_dir / f"{job.job_id}.json"
        checkpoint_path.write_text(json.dumps({
            "job_id": job.job_id,
            "timestamp": time.time(),
            "data": checkpoint_data,
        }, indent=2), encoding="utf-8")
        
        LOGGER.info("Saved checkpoint for job %s", job.job_id)

    def load_checkpoint(self, job: QueueJob) -> dict[str, Any] | None:
        """Load checkpoint cho job (để resume)"""
        checkpoint_path = self.checkpoints_dir / f"{job.job_id}.json"
        if not checkpoint_path.exists():
            return None
        
        try:
            data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            LOGGER.info("Loaded checkpoint for job %s", job.job_id)
            return data.get("data")
        except Exception as exc:
            LOGGER.error("Failed to load checkpoint for job %s: %s", job.job_id, exc)
            return None

    def get_active_job(self) -> QueueJob | None:
        """Lấy job đang chạy hiện tại"""
        if not self.active_lock_path.exists():
            return None
        
        lock_data = self._read_lock()
        if not lock_data:
            return None
        
        job_id = lock_data.get("job_id")
        if not job_id:
            return None
        
        return self._load_job(job_id)

    def update_job_progress(
        self,
        job: QueueJob,
        *,
        current_alpha_id: str | None = None,
        current_alpha_expression: str | None = None,
        current_stage: str | None = None,
        progress_data: dict[str, Any] | None = None,
    ) -> None:
        """Cập nhật progress của job"""
        if current_alpha_id is not None:
            job.current_alpha_id = current_alpha_id
        if current_alpha_expression is not None:
            job.current_alpha_expression = current_alpha_expression
        if current_stage is not None:
            job.current_stage = current_stage
        if progress_data is not None:
            job.progress = {**(job.progress or {}), **progress_data}
        
        self._save_job(job)

    def add_alpha_result(
        self,
        job: QueueJob,
        alpha_id: str,
        expression: str,
        status: str,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """Thêm kết quả alpha vào job"""
        if job.alphas_processed is None:
            job.alphas_processed = []
        
        job.alphas_processed.append({
            "alpha_id": alpha_id,
            "expression": expression[:80],  # Truncate for display
            "status": status,
            "metrics": metrics or {},
            "timestamp": time.time(),
        })
        
        # Track approved/submitted alphas
        if status == "approved":
            if job.alphas_approved is None:
                job.alphas_approved = []
            job.alphas_approved.append(alpha_id)
        elif status == "submitted":
            if job.alphas_submitted is None:
                job.alphas_submitted = []
            job.alphas_submitted.append(alpha_id)
        
        self._save_job(job)

    def get_queue_status(self) -> dict[str, Any]:
        """Lấy trạng thái của hàng đợi"""
        jobs = self._list_jobs()
        active_job = self.get_active_job()
        
        queued_jobs = [j for j in jobs if j.status == "queued"]
        paused_jobs = [j for j in jobs if j.status == "paused"]
        completed_jobs = [j for j in jobs if j.status == "completed"]
        failed_jobs = [j for j in jobs if j.status == "failed"]
        
        return {
            "active_job": active_job.to_dict() if active_job else None,
            "queued_count": len(queued_jobs),
            "paused_count": len(paused_jobs),
            "completed_count": len(completed_jobs),
            "failed_count": len(failed_jobs),
            "queued_jobs": [j.to_dict() for j in sorted(queued_jobs, key=lambda x: x.created_at)[:5]],
            "paused_jobs": [j.to_dict() for j in paused_jobs],
            "recent_completed": [j.to_dict() for j in sorted(completed_jobs, key=lambda x: x.completed_at or 0, reverse=True)[:3]],
            "recent_failed": [j.to_dict() for j in sorted(failed_jobs, key=lambda x: x.completed_at or 0, reverse=True)[:3]],
        }

    def cleanup_old_jobs(self, max_age_seconds: int = 86400 * 7) -> int:
        """Xóa các job cũ (đã hoàn thành hoặc thất bại)"""
        now = time.time()
        jobs = self._list_jobs()
        removed = 0
        
        for job in jobs:
            if job.status in ("completed", "failed"):
                age = now - (job.completed_at or job.created_at)
                if age > max_age_seconds:
                    self._delete_job(job.job_id)
                    removed += 1
        
        if removed > 0:
            LOGGER.info("Cleaned up %d old jobs", removed)
        
        return removed

    def _save_job(self, job: QueueJob) -> None:
        """Lưu job vào file"""
        job_path = self.jobs_dir / f"{job.job_id}.json"
        job_path.write_text(json.dumps(job.to_dict(), indent=2), encoding="utf-8")

    def _load_job(self, job_id: str) -> QueueJob | None:
        """Load job từ file"""
        job_path = self.jobs_dir / f"{job_id}.json"
        if not job_path.exists():
            return None
        
        try:
            data = json.loads(job_path.read_text(encoding="utf-8"))
            return QueueJob.from_dict(data)
        except Exception as exc:
            LOGGER.error("Failed to load job %s: %s", job_id, exc)
            return None

    def _delete_job(self, job_id: str) -> None:
        """Xóa job"""
        job_path = self.jobs_dir / f"{job_id}.json"
        job_path.unlink(missing_ok=True)
        
        checkpoint_path = self.checkpoints_dir / f"{job_id}.json"
        checkpoint_path.unlink(missing_ok=True)

    def _list_jobs(self) -> list[QueueJob]:
        """List tất cả jobs"""
        jobs = []
        for job_file in self.jobs_dir.glob("*.json"):
            job = self._load_job(job_file.stem)
            if job:
                jobs.append(job)
        return jobs

    def _read_lock(self) -> dict[str, Any] | None:
        """Đọc thông tin từ lock file"""
        try:
            data = json.loads(self.active_lock_path.read_text(encoding="utf-8"))
            return data
        except Exception:
            return None

    @staticmethod
    def _process_exists(pid: int) -> bool:
        """Kiểm tra xem process còn tồn tại không"""
        if pid <= 0:
            return False
        
        if os.name != "nt":
            try:
                os.kill(pid, 0)
            except OSError:
                return False
            return True
        
        # Windows
        import ctypes
        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
