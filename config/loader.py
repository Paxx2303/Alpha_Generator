from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
from typing import Any

import yaml


_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


@dataclass(slots=True)
class AppConfig:
    root: Path
    settings: dict[str, Any]
    alpha: dict[str, Any]
    env: dict[str, str]

    @property
    def dry_run(self) -> bool:
        app_value = self.settings.get("app", {}).get("dry_run", True)
        env_value = self.env.get("WQ_DRY_RUN")
        if env_value is not None:
            return env_value.lower() in {"1", "true", "yes", "on"}
        return bool(app_value)

    @property
    def alpha_store_path(self) -> Path:
        return self.root / self.settings["database"]["alpha_store"]

    @property
    def performance_log_path(self) -> Path:
        return self.root / self.settings["database"]["performance_log"]

    @property
    def knowledge_root(self) -> Path:
        return self.root / self.settings["knowledge_base"]["root"]

    @property
    def quality_gate(self) -> dict[str, float]:
        return self.alpha.get("quality_gate", {})

    @property
    def alpha_defaults(self) -> dict[str, Any]:
        return self.alpha.get("defaults", {})


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    env: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip("'").strip('"')
    return env


def _expand_env(value: Any, env: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env(inner, env) for key, inner in value.items()}
    if isinstance(value, list):
        return [_expand_env(item, env) for item in value]
    if isinstance(value, str):
        return _ENV_PATTERN.sub(lambda match: env.get(match.group(1), match.group(0)), value)
    return value


def load_config(root: str | Path | None = None) -> AppConfig:
    project_root = Path(root or Path.cwd()).resolve()
    env_from_file = _parse_env_file(project_root / ".env")
    # Let the active shell override .env so we can safely switch modes per run.
    merged_env = {**env_from_file, **os.environ}

    settings_path = project_root / "config" / "settings.yaml"
    alpha_path = project_root / "config" / "alpha_config.yaml"

    settings = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
    alpha = yaml.safe_load(alpha_path.read_text(encoding="utf-8")) or {}

    settings = _expand_env(settings, merged_env)
    alpha = _expand_env(alpha, merged_env)
    return AppConfig(root=project_root, settings=settings, alpha=alpha, env=merged_env)
