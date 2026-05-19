"""
Theory Researcher
Allows Hermes and DeerFlow to autonomously research new theoretical concepts when needed.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


class TheoryResearcher:
    def __init__(self, knowledge_root: Path):
        self.knowledge_root = Path(knowledge_root)
        self.theory_dirs = [
            self.knowledge_root / "research_feeds" / "reference",
            self.knowledge_root / "lessons_learned",
            self.knowledge_root / "research_papers",
        ]

    def research(self, topic: str, max_results: int = 5) -> str:
        """
        Search for theory documents related to the given topic.
        Returns concatenated relevant snippets.
        """
        topic_lower = topic.lower()
        results: List[str] = []
        count = 0

        for directory in self.theory_dirs:
            if not directory.exists():
                continue
            for file_path in directory.rglob("*.md"):
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
                    if topic_lower in text:
                        # Return first 800 chars of matching file
                        snippet = file_path.read_text(encoding="utf-8", errors="ignore")[:800]
                        results.append(f"--- {file_path.name} ---\n{snippet}")
                        count += 1
                        if count >= max_results:
                            break
                except Exception:
                    continue
            if count >= max_results:
                break

        if not results:
            return f"No additional theory found for topic: {topic}"

        return "\n\n".join(results)

    def get_research_summary(self, topics: List[str]) -> str:
        """Research multiple topics and return combined summary."""
        summaries = []
        for topic in topics:
            summary = self.research(topic, max_results=2)
            summaries.append(f"Topic: {topic}\n{summary}")
        return "\n\n".join(summaries)
