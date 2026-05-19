"""
Data Researcher
Provides Hermes and DeerFlow with characteristics of the data universe
that the generated alpha will operate on.

Primary source: Live data from WorldQuant Brain (when client is provided).
Fallback: Static JSON files or default profiles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import logging

LOGGER = logging.getLogger(__name__)


class DataResearcher:
    def __init__(self, knowledge_root: Path, wq_client: Any | None = None):
        """
        knowledge_root: path to knowledge_base folder
        wq_client: optional WorldQuantClient instance for live data
        """
        self.knowledge_root = Path(knowledge_root)
        self.data_dir = self.knowledge_root / "research_feeds" / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.wq_client = wq_client  # WorldQuantClient instance

    def get_universe_profile(self, universe: str = "TOP3000") -> Dict[str, Any]:
        """Return basic liquidity and coverage profile of the universe."""
        profile_path = self.data_dir / f"{universe.lower()}_profile.json"
        if profile_path.exists():
            try:
                return json.loads(profile_path.read_text())
            except Exception:
                pass

        # Default fallback profile
        return {
            "universe": universe,
            "avg_adv": 2500000,           # Average daily volume
            "median_adv": 1800000,
            "liquidity_tier": "medium-high",
            "coverage": "broad",
            "note": "Fallback profile - update with real data when available"
        }

    def get_field_quality(self, field: str) -> Dict[str, Any]:
        """Return quality and reliability info for a specific data field."""
        field_path = self.data_dir / f"field_quality_{field.lower()}.json"
        if field_path.exists():
            try:
                return json.loads(field_path.read_text())
            except Exception:
                pass

        # Default quality profiles
        defaults = {
            "close": {"reliability": "high", "missing_rate": 0.01, "note": "Most reliable price field"},
            "volume": {"reliability": "medium-high", "missing_rate": 0.03, "note": "Can be noisy on low-liquidity names"},
            "vwap": {"reliability": "high", "missing_rate": 0.02, "note": "Good for execution-aware signals"},
            "returns": {"reliability": "medium", "missing_rate": 0.02, "note": "Derived field - watch for extreme values"},
        }
        return defaults.get(field.lower(), {"reliability": "unknown", "note": "No quality data available"})

    def get_regime_data_context(self) -> str:
        """Return short text describing current data regime (volatility, liquidity)."""
        regime_file = self.data_dir / "current_regime.md"
        if regime_file.exists():
            try:
                return regime_file.read_text()[:800]
            except Exception:
                pass

        return (
            "Current data regime: Normal liquidity, moderate volatility. "
            "Volume signals are generally reliable. Avoid extreme low-liquidity names."
        )

    # ===================== LIVE DATA FROM WORLDQUANT BRAIN =====================

    def _fetch_live_universe_stats(self, universe: str = "TOP3000") -> Dict[str, Any] | None:
        """Try to fetch real universe statistics from WorldQuant Brain."""
        if not self.wq_client:
            return None

        try:
            # Example endpoint (adjust if needed)
            resp = self.wq_client.session.get(
                f"{self.wq_client.base_url}/universes/{universe}/stats",
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                LOGGER.info("Fetched live universe stats for %s", universe)
                return {
                    "universe": universe,
                    "avg_adv": data.get("avg_adv", 0),
                    "median_adv": data.get("median_adv", 0),
                    "liquidity_tier": data.get("liquidity_tier", "medium"),
                    "coverage": data.get("coverage", "broad"),
                    "source": "live_wq_brain",
                }
        except Exception as exc:
            LOGGER.warning("Failed to fetch live universe stats: %s", exc)

        return None

    def _fetch_live_regime_context(self) -> str | None:
        """Try to get current market regime from WorldQuant Brain."""
        if not self.wq_client:
            return None

        try:
            resp = self.wq_client.session.get(
                f"{self.wq_client.base_url}/market/regime",
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                regime = data.get("regime", "normal")
                vol_level = data.get("volatility_level", "medium")
                liq_level = data.get("liquidity_level", "normal")
                return (
                    f"Current regime from WQ Brain: {regime} volatility, "
                    f"{liq_level} liquidity. Volume signals are generally reliable."
                )
        except Exception as exc:
            LOGGER.warning("Failed to fetch live regime: %s", exc)

        return None

    def build_data_context(self, strategy_type: str) -> str:
        """Build a compact data context string. Prefer live data from WorldQuant Brain."""
        # Try live data first
        live_profile = self._fetch_live_universe_stats("TOP3000")
        live_regime = self._fetch_live_regime_context()

        if live_profile:
            profile = live_profile
        else:
            profile = self.get_universe_profile("TOP3000")

        regime = live_regime or self.get_regime_data_context()

        context = (
            f"DATA UNIVERSE: {profile.get('universe', 'TOP3000')}\n"
            f"Avg Daily Volume: {profile.get('avg_adv', 'N/A')}\n"
            f"Liquidity: {profile.get('liquidity_tier', 'medium')}\n"
            f"Source: {profile.get('source', 'static')}\n\n"
            f"REGIME:\n{regime}\n\n"
            f"STRATEGY FOCUS: {strategy_type}\n"
            "Recommendation: Prefer volume + volatility normalized signals in current regime."
        )
        return context
