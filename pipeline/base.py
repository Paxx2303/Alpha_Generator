# pipeline/base.py — Shared base classes for all pipeline steps
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StepResult:
    """Returned by every pipeline step's .run() method."""
    success: bool
    summary: str
    error: Optional[str] = None
    stats: dict = field(default_factory=dict)
