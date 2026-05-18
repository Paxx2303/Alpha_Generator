from __future__ import annotations

from .rag_loader import WQKnowledgeBase


def get_generation_context(root: str, strategy_type: str) -> str:
    kb = WQKnowledgeBase(root)
    kb.load_all()
    alpha_context = kb.get_alpha_context(strategy_type)
    failure_context = kb.get_failure_context()
    return f"{alpha_context}\n\nFailure patterns:\n{failure_context}"
