"""
Alpha Theory RAG Module
Provides theory-grounded retrieval for Hermes and DeerFlow during generation and review.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


THEORY_FILES = [
    "research_feeds/reference/trading_volume_alpha_nber_2024.md",
    "research_feeds/reference/alphaforge_dynamic_combination_2024.md",
    "research_feeds/reference/llm_mcts_alpha_mining_2025.md",
    "lessons_learned/operator_risk_matrix.md",
    "lessons_learned/regime_aware_generation.md",
    "lessons_learned/turnover_optimization.md",          # future file
    "research_feeds/reference/alpha_decay_signal_erosion.md",  # future file
]


def load_theory_snippets(knowledge_root: Path, max_chars: int = 6000) -> str:
    """
    Load and concatenate key theory documents for RAG injection.
    Returns a single string suitable for prompt context.
    """
    snippets: List[str] = []
    total = 0

    for rel_path in THEORY_FILES:
        file_path = knowledge_root / rel_path
        if not file_path.exists():
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            # Take first 1200 chars of each file to keep context manageable
            chunk = text[:1200].strip()
            if chunk:
                snippets.append(f"--- {rel_path} ---\n{chunk}")
                total += len(chunk)
                if total >= max_chars:
                    break
        except Exception:
            continue

    if not snippets:
        return "No theory documents found. Rely on general quant knowledge."

    return "\n\n".join(snippets)


def get_theory_context_for_generation(knowledge_root: Path, strategy_type: str) -> str:
    """
    Returns theory context specifically optimized for alpha generation.
    """
    base = load_theory_snippets(knowledge_root, max_chars=4500)
    header = (
        f"Theory Grounding for {strategy_type.upper()} Alpha Generation:\n"
        "Use the following principles when creating expressions:\n"
        "- Fitness-first optimization\n"
        "- Volume as predictor\n"
        "- Regime awareness\n"
        "- Operator risk control\n"
        "- Avoid motif repetition\n\n"
    )
    return header + base


def get_theory_context_for_review(knowledge_root: Path) -> str:
    """
    Returns theory context for post-simulation review.
    """
    base = load_theory_snippets(knowledge_root, max_chars=3500)
    header = (
        "Theory Checklist for Alpha Review:\n"
        "1. Economic hypothesis\n"
        "2. Regime fit\n"
        "3. Decay risk\n"
        "4. Turnover realism\n"
        "5. Motif repetition\n\n"
    )
    return header + base
