from __future__ import annotations

import logging
import subprocess
import shutil

from .openai_fallback import OpenAIFallbackClient
from pipeline.models import AgentReview, AlphaCandidate, SimulationMetrics


LOGGER = logging.getLogger(__name__)
RUN_TIMEOUT_SECONDS = 90
MEMORY_TIMEOUT_SECONDS = 10


def _estimate_confidence(text: str, verdict: str) -> float:
    score_map = {"PASS": 0.76, "WARN": 0.56, "FAIL": 0.38}
    score = score_map.get(verdict, 0.5)
    lower = text.lower()
    positive_cues = ("strong", "clear", "conviction", "high confidence", "robust", "compelling")
    caution_cues = ("uncertain", "mixed", "unclear", "maybe", "weak", "fragile", "tentative")
    if any(cue in lower for cue in positive_cues):
        score += 0.08
    if any(cue in lower for cue in caution_cues):
        score -= 0.08
    return max(0.05, min(0.95, round(score, 3)))


class HermesBridge:
    def __init__(
        self,
        command: str = "hermes",
        enabled: bool = True,
        container_name: str = "wq-hermes-agent",
        container_binary: str = "/opt/hermes/hermes",
        fallback_client: OpenAIFallbackClient | None = None,
    ) -> None:
        self.command = command
        self.enabled = enabled
        self.container_name = container_name
        self.container_binary = container_binary
        self.fallback_client = fallback_client

    def available(self) -> bool:
        return self.enabled and (shutil.which(self.command) is not None or self._container_running())

    def ask(self, prompt: str) -> str:
        if not self.available():
            LOGGER.info("Hermes unavailable; falling back to local heuristic response.")
            return (
                "rank(ts_mean(returns, 10))\n"
                "rank(close / ts_mean(close, 20) - 1)\n"
                "rank(ts_delta(volume, 5) * -ts_delta(close, 5))"
            )

        try:
            completed = self._run_prompt(prompt)
        except subprocess.TimeoutExpired:
            fallback = self._fallback(prompt, "Hermes timed out.", force=True)
            if fallback:
                return fallback
            LOGGER.warning("Hermes timed out; using fallback output.")
            return "rank(ts_mean(returns, 10))"
        if completed.returncode != 0:
            error_text = "\n".join(
                part.strip()
                for part in (completed.stderr, completed.stdout)
                if isinstance(part, str) and part.strip()
            )
            fallback = self._fallback(prompt, error_text, force=True)
            if fallback:
                return fallback
            LOGGER.warning("Hermes command failed; using fallback output. stderr=%s", completed.stderr.strip())
            return "rank(ts_mean(returns, 10))"
        result = completed.stdout.strip()
        if not result:
            fallback = self._fallback(prompt, "Hermes returned empty output.", force=True)
            if fallback:
                return fallback
        fallback = self._fallback(
            prompt,
            "\n".join(
                part.strip()
                for part in (completed.stderr, result)
                if isinstance(part, str) and part.strip()
            ),
        )
        if fallback:
            return fallback
        return result

    def remember(self, text: str) -> None:
        if not self.available():
            return
        try:
            if self._container_running():
                subprocess.run(
                    ["docker", "exec", "-i", self.container_name, self.container_binary, "memory", "add", text],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=MEMORY_TIMEOUT_SECONDS,
                )
                return
            if shutil.which(self.command) is not None:
                subprocess.run(
                    [self.command, "memory", "add", text],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=MEMORY_TIMEOUT_SECONDS,
                )
        except subprocess.TimeoutExpired:
            LOGGER.warning("Hermes memory update timed out; continuing without persistence.")

    def review_alpha(
        self,
        candidate: AlphaCandidate,
        stage: str,
        context: str,
        metrics: SimulationMetrics | None = None,
    ) -> AgentReview:
        prompt = (
            f"You are reviewing a WorldQuant alpha at stage={stage}.\n"
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
        prompt += (
            "Return a short verdict line in the form PASS/WARN/FAIL, then one short paragraph of reasons.\n"
            f"Context:\n{context[:4000]}"
        )
        result = self.ask(prompt).strip()
        verdict = "WARN"
        upper = result.upper()
        if "FAIL" in upper:
            verdict = "FAIL"
        elif "PASS" in upper:
            verdict = "PASS"
        return AgentReview(
            agent="hermes",
            stage=stage,
            verdict=verdict,
            summary=result[:1200],
            confidence=_estimate_confidence(result, verdict),
        )

    def _fallback(self, prompt: str, error_text: str, force: bool = False) -> str:
        if not self.fallback_client or not self.fallback_client.available():
            return ""
        if not force and error_text and not self.fallback_client.should_fallback(error_text):
            return ""
        LOGGER.warning("Hermes falling back to OpenRouter model %s", self.fallback_client.model)
        return self.fallback_client.chat(prompt)

    def _run_prompt(self, prompt: str) -> subprocess.CompletedProcess[str]:
        if self._container_running():
            return subprocess.run(
                ["docker", "exec", "-i", self.container_name, self.container_binary, "-z", prompt],
                capture_output=True,
                text=True,
                check=False,
                timeout=RUN_TIMEOUT_SECONDS,
            )
        return subprocess.run(
            [self.command, "-z", prompt],
            capture_output=True,
            text=True,
            check=False,
            timeout=RUN_TIMEOUT_SECONDS,
        )

    def _container_running(self) -> bool:
        completed = subprocess.run(
            ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        return self.container_name in completed.stdout.splitlines()
