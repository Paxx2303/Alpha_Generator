from __future__ import annotations

from dataclasses import dataclass

from .deerflow_bridge import DeerFlowBridge


@dataclass
class TaskRouter:
    deerflow: DeerFlowBridge

    def route(self, task_type: str) -> str:
        return "deerflow"
