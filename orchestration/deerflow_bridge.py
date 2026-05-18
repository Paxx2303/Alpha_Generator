from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import uuid

import requests

from .openai_fallback import OpenAIFallbackClient
from pipeline.models import AgentReview, AlphaCandidate, SimulationMetrics


LOGGER = logging.getLogger(__name__)


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

    def run_research(self, task: str) -> str:
        if not self.available():
            LOGGER.info("DeerFlow unavailable; returning mock research summary.")
            return (
                "Recent themes: short-horizon momentum with sector neutralization, "
                "volume-confirmed reversals, and hybrid price-volume rank operators."
            )

        gateway_running = self._gateway_running()
        if gateway_running:
            result = self._run_via_gateway(task)
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
    ) -> AgentReview:
        if not self.available():
            summary = (
                f"DeerFlow unavailable at {stage}; local fallback suggests reviewing "
                f"turnover, self-correlation, and operator diversity for {candidate.expression}."
            )
            return AgentReview(agent="deerflow", stage=stage, verdict="WARN", summary=summary, confidence=0.42)

        prompt = (
            f"Review this WorldQuant alpha at stage={stage}.\n"
            f"Expression: {candidate.expression}\n"
            f"Strategy type: {candidate.strategy_type}\n"
            f"Metadata: {candidate.metadata}\n"
        )
        if metrics is not None:
            prompt += (
                f"Metrics: sharpe={metrics.sharpe}, fitness={metrics.fitness}, returns={metrics.annual_returns}, "
                f"turnover={metrics.turnover}, drawdown={metrics.drawdown}, self_corr={metrics.self_correlation}\n"
                f"Checks: {metrics.checks}\n"
            )
        prompt += "Respond with PASS/WARN/FAIL and concise reasoning."
        result = self.run_research(prompt) or "WARN: DeerFlow returned no structured review."
        verdict = "WARN"
        upper = result.upper()
        if "FAIL" in upper:
            verdict = "FAIL"
        elif "PASS" in upper:
            verdict = "PASS"
        return AgentReview(
            agent="deerflow",
            stage=stage,
            verdict=verdict,
            summary=result[:1200],
            confidence=_estimate_confidence(result, verdict),
        )

    def _run_via_gateway(self, task: str) -> str:
        prompt = task.strip()
        if "DO NOT CALL TOOLS" not in prompt.upper():
            prompt += "\n\nReply in plain text only. Do not call tools."
        payload = {
            "messages": [{"role": "user", "content": prompt}],
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
                timeout=(10, 180),
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
                    if event.get("finish_reason"):
                        break
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
        return self.fallback_client.chat(prompt)

    def _gateway_running(self) -> bool:
        completed = subprocess.run(
            ["docker", "ps", "--filter", f"name={self.gateway_container}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        return self.gateway_container in completed.stdout.splitlines()
