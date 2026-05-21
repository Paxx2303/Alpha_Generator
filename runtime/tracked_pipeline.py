"""
Tracked Pipeline - Wrapper cho AlphaPipeline để tự động cập nhật trạng thái vào queue.
"""

from __future__ import annotations

import logging
from typing import Any

from pipeline.alpha_pipeline import AlphaPipeline
from pipeline.models import AlphaCandidate, EvaluatedAlpha
from runtime.queue_manager import QueueJob, QueueManager

LOGGER = logging.getLogger(__name__)


class TrackedPipeline:
    """
    Wrapper cho AlphaPipeline để tự động cập nhật trạng thái vào queue.
    
    Mỗi khi pipeline xử lý một alpha, trạng thái sẽ được cập nhật vào job.
    """

    def __init__(self, pipeline: AlphaPipeline, queue_manager: QueueManager, job: QueueJob):
        self.pipeline = pipeline
        self.queue_manager = queue_manager
        self.job = job
        
        # Monkey patch các methods để track progress
        self._patch_pipeline()

    def _patch_pipeline(self) -> None:
        """Patch các methods của pipeline để track progress"""
        # Patch simulator.run
        original_simulator_run = self.pipeline.simulator.run
        
        def tracked_simulator_run(candidate: AlphaCandidate):
            # Update job với alpha đang được simulate
            self.queue_manager.update_job_progress(
                self.job,
                current_alpha_expression=candidate.expression,
                current_stage="simulation",
            )
            
            # Run simulation
            result = original_simulator_run(candidate)
            
            return result
        
        self.pipeline.simulator.run = tracked_simulator_run
        
        # Patch store.insert_alpha
        original_insert_alpha = self.pipeline.store.insert_alpha
        
        def tracked_insert_alpha(candidate, metrics, status, **kwargs):
            # Insert alpha
            alpha_id = original_insert_alpha(candidate, metrics, status, **kwargs)
            
            # Update job với kết quả alpha
            self.queue_manager.add_alpha_result(
                self.job,
                alpha_id=alpha_id,
                expression=candidate.expression,
                status=status,
                metrics={
                    "sharpe": metrics.sharpe,
                    "fitness": metrics.fitness,
                    "turnover": metrics.turnover,
                } if metrics else None,
            )
            
            # Update current alpha ID
            self.queue_manager.update_job_progress(
                self.job,
                current_alpha_id=alpha_id,
            )
            
            return alpha_id
        
        self.pipeline.store.insert_alpha = tracked_insert_alpha

    def run_once(
        self,
        strategy_type: str | None = None,
        count: int | None = None,
        submit_enabled: bool = True,
    ) -> dict[str, Any]:
        """Run pipeline với tracking"""
        # Update job stage
        self.queue_manager.update_job_progress(
            self.job,
            current_stage="research",
        )
        
        # Run pipeline
        result = self.pipeline.run_once(
            strategy_type=strategy_type,
            count=count,
            submit_enabled=submit_enabled,
        )
        
        # Update final progress
        self.queue_manager.update_job_progress(
            self.job,
            current_stage="completed",
            progress_data={
                "tested": result.get("tested", 0),
                "approved": len(result.get("approved", [])),
            },
        )
        
        return result
