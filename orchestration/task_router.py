from __future__ import annotations

from dataclasses import dataclass

from .deerflow_bridge import DeerFlowBridge
from .hermes_bridge import HermesBridge


@dataclass
class TaskRouter:
    hermes: HermesBridge
    deerflow: DeerFlowBridge

    def route(self, task_type: str) -> str:
        research_tasks = {"research", "paper_scrape", "market_scan"}
        memory_tasks = {"lesson_update", "skill_generation", "llm_generation"}
        if task_type in research_tasks and self.deerflow.available():
            return "deerflow"
        if task_type in memory_tasks and self.hermes.available():
            return "hermes"
        return "local"
