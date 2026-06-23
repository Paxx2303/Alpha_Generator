"""
operation/research_daemon.py — Autonomous alpha research daemon.

Rotates through WQB market settings:
  • Rotate when: 1 gold alpha found (goal met) OR 1 hour elapsed (timeout)
  • Calls DeerFlow research API with current setting embedded in the prompt
  • DeerFlow handles the full empirical research loop (SKILL.md)

Run: python operation/research_daemon.py
Systemd: see deploy/vm-setup.sh for service setup
"""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
UTC = timezone.utc
from pathlib import Path

import requests

_ROOT = Path(__file__).parent.parent

_LOG_DIR = Path("/app/logs") if Path("/app/logs").exists() else _ROOT / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [daemon] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(_LOG_DIR / "research-daemon.log"), mode="a"),
    ],
)
log = logging.getLogger(__name__)
STATE_PATH = _ROOT / "data" / "research_state.json"
DEERFLOW_API = os.getenv("DEERFLOW_GATEWAY_URL", "http://localhost:8001")
INTERNAL_TOKEN = os.getenv("DEER_FLOW_INTERNAL_AUTH_TOKEN", "")

# Full WQB market rotation — ordered by empirical priority (best settings first)
# Format: "UNIVERSE|NEUTRALIZATION|DECAY|TRUNCATION"
MARKET_ROTATION = [
    "TOP1000|INDUSTRY|3|0.08",       # Highest empirical pass rate
    "TOP1000|SUBINDUSTRY|3|0.08",
    "TOP1000|SECTOR|3|0.08",
    "TOP1000|MARKET|3|0.08",
    "TOP1000|NONE|3|0.08",
    "TOP3000|INDUSTRY|3|0.08",
    "TOP3000|SUBINDUSTRY|3|0.08",
    "TOP3000|SECTOR|3|0.08",
    "TOP3000|MARKET|3|0.08",
    "TOP3000|NONE|3|0.08",
    "TOP2000|INDUSTRY|3|0.08",
    "TOP2000|SUBINDUSTRY|3|0.08",
    "TOP500|INDUSTRY|3|0.08",
    "TOP500|SUBINDUSTRY|3|0.08",
    "TOP200|INDUSTRY|3|0.08",
]

ROTATION_INTERVAL = 3600   # seconds — max 1 hour per setting
POLL_INTERVAL    = 120     # seconds — check gold count every 2 min
GOLD_TARGET      = 1       # rotate when this many golds found this session


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {
        "setting_index": 0,
        "current_setting": MARKET_ROTATION[0],
        "gold_count_this_session": 0,
        "session_started_at": datetime.now(UTC).isoformat(),
        "total_golds_found": 0,
        "total_sessions": 0,
    }


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_gold_count_in_db() -> int:
    try:
        sys.path.insert(0, str(_ROOT))
        from storage.store import Store
        s = Store()
        alphas = s.get_gold_alphas()
        s.close()
        return len(alphas) if alphas else 0
    except Exception as e:
        log.warning(f"Could not read gold count: {e}")
        return 0


def call_deerflow_research(setting: str) -> bool:
    """
    Trigger a DeerFlow research session for the given market setting.
    Calls gateway directly on localhost:8001 (exposed by docker-compose.override.yml)
    so we bypass nginx auth. Returns True if DeerFlow accepted the task.
    """
    universe, neutralization, decay, truncation = setting.split("|")
    prompt = (
        f"Run an empirical alpha research session following the SKILL.md workflow. "
        f"Current market setting: universe={universe}, neutralization={neutralization}, "
        f"decay={decay}, truncation={truncation}. "
        f"Goal: find 1 gold alpha (Sharpe≥1.25, Fitness≥1.0, Turnover 10-70%) "
        f"that passes all IS checks including self-correlation. "
        f"Test at least 5 formula variations. "
        f"Call get_skill_knowledge first to check existing theories for this setting, "
        f"then compare backtest results against those theories after each test."
    )
    try:
        # X-Internal-Token bypasses DeerFlow's CSRF check for server-to-server calls.
        headers = {"X-Internal-Token": INTERNAL_TOKEN} if INTERNAL_TOKEN else {}

        # Ultra mode: 5 plan iterations, 30 steps, background investigation.
        # We trigger the stream and don't consume it — DeerFlow researches in Docker.
        with requests.post(
            f"{DEERFLOW_API}/api/chat/stream",
            json={
                "messages": [{"role": "user", "content": prompt}],
                "max_plan_iterations": 5,
                "max_step_num": 30,
                "enable_background_investigation": True,
            },
            headers=headers,
            stream=True,
            timeout=60,
        ) as res:
            if res.status_code == 200:
                # Read first chunk to confirm stream started, then release
                for chunk in res.iter_content(chunk_size=256):
                    if chunk:
                        break
                log.info(f"DeerFlow research triggered for {setting}")
                return True
            log.warning(f"DeerFlow returned {res.status_code}: {res.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        log.warning(f"DeerFlow not reachable at {DEERFLOW_API} — research cycle skipped")
        return False
    except Exception as e:
        log.error(f"DeerFlow call failed: {e}")
        return False


def rotate_setting(state: dict) -> dict:
    next_idx = (state["setting_index"] + 1) % len(MARKET_ROTATION)
    new_setting = MARKET_ROTATION[next_idx]
    log.info(f"Rotating: {state['current_setting']} → {new_setting} "
             f"(golds this session: {state['gold_count_this_session']})")
    state.update({
        "setting_index": next_idx,
        "current_setting": new_setting,
        "gold_count_this_session": 0,
        "session_started_at": datetime.now(UTC).isoformat(),
        "total_sessions": state.get("total_sessions", 0) + 1,
    })
    return state


def should_rotate(state: dict, gold_count: int) -> str:
    """Returns 'gold_target' | 'timeout' | None"""
    golds_this_session = gold_count - state.get("_baseline_golds", 0)
    if golds_this_session >= GOLD_TARGET:
        return "gold_target"
    started = datetime.fromisoformat(state["session_started_at"])
    elapsed = (datetime.now(UTC) - started).total_seconds()
    if elapsed >= ROTATION_INTERVAL:
        return "timeout"
    return None


def run():
    log.info("=== Alpha Research Daemon started ===")
    log.info(f"Settings in rotation: {len(MARKET_ROTATION)}")
    log.info(f"Goal: {GOLD_TARGET} gold alpha per setting, max {ROTATION_INTERVAL}s")

    state = load_state()
    baseline_golds = get_gold_count_in_db()
    state["_baseline_golds"] = baseline_golds
    save_state(state)

    log.info(f"Starting with setting: {state['current_setting']} "
             f"(baseline gold count: {baseline_golds})")

    # Trigger first research session
    call_deerflow_research(state["current_setting"])

    while True:
        time.sleep(POLL_INTERVAL)

        current_golds = get_gold_count_in_db()
        reason = should_rotate(state, current_golds)

        if reason:
            state["total_golds_found"] = state.get("total_golds_found", 0) + (
                current_golds - state.get("_baseline_golds", 0)
            )
            log.info(f"Rotation trigger: {reason} | "
                     f"Setting: {state['current_setting']} | "
                     f"New golds: {current_golds - state.get('_baseline_golds', 0)}")

            state = rotate_setting(state)
            state["_baseline_golds"] = current_golds
            save_state(state)

            call_deerflow_research(state["current_setting"])
        else:
            started = datetime.fromisoformat(state["session_started_at"])
            elapsed = int((datetime.now(UTC) - started).total_seconds())
            golds_this_session = current_golds - state.get("_baseline_golds", 0)
            log.info(f"Setting: {state['current_setting']} | "
                     f"Elapsed: {elapsed}s/{ROTATION_INTERVAL}s | "
                     f"Golds this session: {golds_this_session}/{GOLD_TARGET} | "
                     f"Total golds: {current_golds}")
            save_state(state)


if __name__ == "__main__":
    run()
