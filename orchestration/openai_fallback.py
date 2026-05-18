from __future__ import annotations

import logging

import requests


LOGGER = logging.getLogger(__name__)

FALLBACK_ERROR_MARKERS = (
    "freeusagelimiterror",
    "rate limit exceeded",
    "rate_limit_exceeded",
    "out of credits",
    "insufficient credits",
    '"code":402',
    '"code":429',
)


class OpenAIFallbackClient:
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openrouter/owl-alpha",
        enabled: bool = True,
        app_name: str = "Alpha_Generator",
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.enabled = enabled
        self.app_name = app_name

    def available(self) -> bool:
        return self.enabled and bool(self.api_key and self.base_url and self.model)

    def should_fallback(self, error_text: str) -> bool:
        normalized = error_text.lower()
        return any(marker in normalized for marker in FALLBACK_ERROR_MARKERS)

    def chat(self, prompt: str) -> str:
        if not self.available():
            return ""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://local.alpha-generator",
            "X-OpenRouter-Title": self.app_name,
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            LOGGER.warning("OpenRouter fallback request failed: %s", exc)
            return ""

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError):
            LOGGER.warning("OpenRouter fallback response was missing content.")
            return ""
