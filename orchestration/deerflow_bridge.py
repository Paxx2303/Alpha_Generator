from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import requests

from .openai_fallback import OpenAIFallbackClient
from pipeline.models import AgentReview, AlphaCandidate, SimulationMetrics
from knowledge_base.alpha_theory_rag import get_theory_context_for_review
from knowledge_base.theory_researcher import TheoryResearcher
from knowledge_base.data_researcher import DataResearcher


LOGGER = logging.getLogger(__name__)
RESEARCH_TIMEOUT_SECONDS = 180
REVIEW_TIMEOUT_SECONDS = 45


def _estimate_confidence(text: str, verdict: str) -> float:
    score_map = {"PASS": 0.74, "WARN": 0.55, "FAIL": 0.36}
    score = score_map.get(verdict, 0.5)
    lower = text.lower()
    positive_cues = ("strong", "clear", "conviction", "high confidence", "robust", "compelling")
    caution_cues = ("uncertain", "mixed", "unclear", "maybe", "weak", "fragile", "tentative")
    if any(cue in lower for cue in positive_cues):
        score += 0.08
    if any(cue in lower for cue in caution_cues):
        score -= 0.08
    return max(0.05, min(0.95, round(score, 3)))


class DeerFlowBridge:
    def __init__(
        self,
        command: str = "deerflow",
        enabled: bool = True,
        config_path: str | None = None,
        project_root: str | None = None,
        gateway_container: str = "deerflow-agent",
        gateway_url: str = "http://localhost:8010/api/chat/stream",
        model: str | None = None,
        fallback_client: OpenAIFallbackClient | None = None,
    ) -> None:
        self.command = command
        self.enabled = enabled
        self.config_path = config_path
        self.project_root = project_root
        self.gateway_container = gateway_container
        self.gateway_url = gateway_url
        self.model = model
        self.fallback_client = fallback_client

    def available(self) -> bool:
        return self.enabled and (shutil.which(self.command) is not None or self._gateway_running())

    def run_research(self, task: str, timeout_seconds: int = RESEARCH_TIMEOUT_SECONDS) -> str:
        if not self.available():
            LOGGER.info("DeerFlow unavailable; returning mock research summary.")
            return (
                "Recent themes: short-horizon momentum with sector neutralization, "
                "volume-confirmed reversals, and hybrid price-volume rank operators."
            )

        gateway_running = self._gateway_running()
        if gateway_running:
            result = self._run_via_gateway(task, timeout_seconds=timeout_seconds)
            if result:
                return result
            fallback = self._fallback(task, "deerflow gateway returned no text", force=True)
            if fallback:
                return fallback
            if shutil.which(self.command) is None:
                LOGGER.warning("DeerFlow gateway returned no text and local CLI is unavailable.")
                return ""

        if shutil.which(self.command) is None:
            LOGGER.warning("DeerFlow CLI is unavailable; returning empty summary.")
            return ""

        env = None
        if self.config_path or self.project_root:
            env = dict(os.environ)
            if self.config_path:
                env["DEER_FLOW_CONFIG_PATH"] = self.config_path
            if self.project_root:
                env["DEER_FLOW_PROJECT_ROOT"] = self.project_root

        completed = subprocess.run(
            [self.command, "run", task],
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
            env=env,
        )
        if completed.returncode != 0:
            fallback = self._fallback(task, "\n".join([completed.stderr.strip(), completed.stdout.strip()]))
            if fallback:
                return fallback
            LOGGER.warning("DeerFlow task failed; returning empty summary.")
            return ""
        return completed.stdout.strip()

    def review_alpha(
        self,
        candidate: AlphaCandidate,
        stage: str,
        context: str,
        metrics: SimulationMetrics | None = None,
        knowledge_root: Path | None = None,
    ) -> AgentReview:
        LOGGER.info(
            "DeerFlow review started; stage=%s strategy=%s expression=%s.",
            stage,
            candidate.strategy_type,
            candidate.expression[:180],
        )
        if not self.available():
            summary = (
                f"DeerFlow unavailable at {stage}; local fallback suggests reviewing "
                f"turnover, self-correlation, and operator diversity for {candidate.expression}."
            )
            review = AgentReview(agent="deerflow", stage=stage, verdict="WARN", summary=summary, confidence=0.42)
            LOGGER.info(
                "DeerFlow review completed; stage=%s verdict=%s confidence=%.3f expression=%s.",
                stage,
                review.verdict,
                review.confidence,
                candidate.expression[:180],
            )
            return review

        theory = ""
        if knowledge_root:
            theory = get_theory_context_for_review(knowledge_root)

        prompt = (
            f"Review this WorldQuant alpha at stage={stage}.\n"
            f"Expression: {candidate.expression}\n"
            f"Strategy: {candidate.strategy_type}\n"
        )
        if metrics is not None:
            prompt += (
                f"Metrics: Sharpe={metrics.sharpe:.2f}, Fitness={metrics.fitness:.2f}, "
                f"Turnover={metrics.turnover:.2f}, SelfCorr={metrics.self_correlation:.2f}\n"
            )
        prompt += (
            "THEORY CHECKLIST:\n"
            "1. Clear economic hypothesis?\n"
            "2. Regime robustness?\n"
            "3. Alpha decay risk?\n"
            "4. Turnover realistic?\n"
            "5. Motif repetition?\n\n"
            f"Theory Grounding (RAG):\n{theory}\n\n"
            "Return VERDICT + brief reasoning."
        )
        result = self.run_research(prompt, timeout_seconds=REVIEW_TIMEOUT_SECONDS) or "WARN: DeerFlow returned no structured review."
        verdict = "WARN"
        upper = result.upper()
        if "FAIL" in upper:
            verdict = "FAIL"
        elif "PASS" in upper:
            verdict = "PASS"
        review = AgentReview(
            agent="deerflow",
            stage=stage,
            verdict=verdict,
            summary=result[:1200],
            confidence=_estimate_confidence(result, verdict),
        )
        LOGGER.info(
            "DeerFlow review completed; stage=%s verdict=%s confidence=%.3f expression=%s.",
            stage,
            review.verdict,
            review.confidence,
            candidate.expression[:180],
        )
        return review

    def _get_skills_context(self) -> str:
        root_dir = Path(self.project_root) if self.project_root else Path(__file__).resolve().parents[1]
        skills_dir = root_dir / "skills"
        if not skills_dir.exists():
            return "No skills found."
        
        context_parts = []
        for path in sorted(skills_dir.glob("*.md")):
            try:
                content = path.read_text(encoding="utf-8", errors="ignore").strip()
                context_parts.append(f"Skill file: {path.name}\n{content}\n")
            except Exception as e:
                LOGGER.warning("Failed to read skill file %s: %s", path.name, e)
        return "\n---\n".join(context_parts)

    def _get_system_prompt(self) -> str:
        skills_context = self._get_skills_context()
        return (
            "You are DeerFlow, a state-of-the-art quantitative research AI agent designed for the WorldQuant Brain platform.\n"
            "The Hermes agent has been completely removed from this system; you are the sole agent responsible for researching, building, reviewing, and optimizing alphas.\n\n"
            "Here are the existing agent skills and files located in the project's 'skills/' directory:\n"
            f"{skills_context}\n\n"
            "Core Rules for Alpha Expressions:\n"
            "1. Valid Operators only: ts_corr, ts_covariance, ts_rank, ts_scale, ts_arg_max, ts_arg_min, ts_decay_linear, ts_mean, ts_std_dev, ts_delta, ts_delay, ts_zscore, ts_regression, ts_sum, ts_av_diff, ts_backfill, trade_when, rank, normalize, zscore, winsorize, scale, quantile, group_neutralize, group_rank, group_zscore, abs, log, sign, sqrt, power, max, min, if_else.\n"
            "2. Forbidden Operators: ts_log_returns, ts_min, ts_max, delay, stddev, correlation, delta.\n\n"
            "When replying in Vietnamese, you MUST adhere to these terminology rules:\n"
            "- Keep 'Sharpe' or 'Sharpe ratio' as 'Sharpe' (NEVER translate to 'sắc nét', 'nhọn', or 'nhạy bén').\n"
            "- Keep 'Fitness' as 'Fitness' (NEVER translate to 'thể hình' or 'thể lực').\n"
            "- Translate 'Turnover' to 'Tỷ lệ vòng quay giao dịch' or keep as 'Turnover' (NEVER translate to 'doanh thu').\n"
            "- Translate 'Turnover band' to 'Dải vòng quay giao dịch' or 'Turnover band' (NEVER translate to 'doanh thu của ban nhạc').\n"
            "- Translate 'Drawdown' to 'Mức sụt giảm tài sản (Drawdown)'.\n"
            "- Keep 'ts_decay_linear' or translate to 'Suy giảm tuyến tính' (NEVER translate to 'Phân rã tuyến tính' or 'phân rã Tuyến').\n"
            "- Keep 'Neutralization' or translate to 'Trung hòa (Neutralization)'.\n"
            "- Translate 'Lookback' to 'Khoảng thời gian nhìn lại' or 'Lookback window'.\n\n"
            "Formatting Guidelines for your responses:\n"
            "- Always format markdown tables cleanly with proper header separators (e.g. | Header 1 | Header 2 | followed by |---|---|).\n"
            "- Ensure clear spacing and visual separation between sections.\n"
            "- Avoid raw code concatenation; use proper markdown blocks with syntax highlighting where appropriate."
        )

    def _run_via_gateway(self, task: str, timeout_seconds: int = RESEARCH_TIMEOUT_SECONDS) -> str:
        prompt = task.strip()
        if "DO NOT CALL TOOLS" not in prompt.upper():
            prompt += "\n\nReply in plain text only. Do not call tools."
        payload = {
            "messages": [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            "chat_session_id": f"alpha-generator-{uuid.uuid4()}",
            "files": [],
            "enable_background_investigation": False,
        }
        if self.model:
            payload["model"] = self.model

        chunks: list[str] = []
        try:
            with requests.post(
                self.gateway_url,
                json=payload,
                stream=True,
                timeout=(10, timeout_seconds),
            ) as response:
                response.raise_for_status()
                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line or not raw_line.startswith("data: "):
                        continue
                    data = raw_line[6:]
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    content = event.get("content")
                    if isinstance(content, str) and content:
                        chunks.append(content)
        except requests.RequestException as exc:
            fallback = self._fallback(task, str(exc), force=True)
            if fallback:
                return fallback
            LOGGER.warning("DeerFlow gateway request failed: %s", exc)
            return ""

        return "".join(chunks).strip()

    def _fallback(self, prompt: str, error_text: str, force: bool = False) -> str:
        if not self.fallback_client or not self.fallback_client.available():
            return ""
        if not force and error_text and not self.fallback_client.should_fallback(error_text):
            return ""
        LOGGER.warning("DeerFlow falling back to OpenRouter model %s", self.fallback_client.model)
        return self.fallback_client.chat(prompt, system_prompt=self._get_system_prompt())

    def research_new_theory(self, topic: str, knowledge_root: Path) -> str:
        """DeerFlow can autonomously research new theoretical topics."""
        researcher = TheoryResearcher(knowledge_root)
        return researcher.research(topic, max_results=4)

    def research_data_context(self, knowledge_root: Path, strategy_type: str = "momentum") -> str:
        """DeerFlow can research data characteristics for the target universe."""
        data_researcher = DataResearcher(knowledge_root)
        return data_researcher.build_data_context(strategy_type)

    def _gateway_running(self) -> bool:
        completed = subprocess.run(
            ["docker", "ps", "--filter", f"name={self.gateway_container}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        return self.gateway_container in completed.stdout.splitlines()
