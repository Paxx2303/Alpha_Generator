"""
operation/runner.py — Alpha research cycle runner.

Calls DeerFlow HTTP API to start a research cycle, streams the response,
and writes data/research_status.json so the dashboard stays up-to-date.

Usage (manual):
    python operation/runner.py
    python operation/runner.py --dry-run    # validate config only

Cronjob (on alpha-vm, every 6 hours):
    0 */6 * * * cd /app/alpha-generator && python operation/runner.py >> /app/logs/runner.log 2>&1
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, UTC
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
STATUS_FILE = DATA_DIR / "research_status.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [runner] %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

RESEARCH_PROMPT = """
Start a new alpha research cycle following the Alpha Research Skill workflow:

1. Call get_skill_knowledge to load current operator rules and patterns.
2. Call get_gold_alphas to know which signal families already pass (avoid correlation > 0.7).
3. Pick ONE unexplored hypothesis from the signal families NOT yet covered:
   - Cross-sectional earnings quality (accruals, cashflow quality)
   - Short-term analyst estimate revisions
   - Institutional flow (short interest, insider activity)
4. Verify required fields exist via search_data_fields.
5. Translate hypothesis to WQB formula and test via submit_alpha.
6. If fail, call diagnose_alpha and try ONE mutation via mutate_formula.
7. Call save_theory with the key insight from this session (pass or fail).

Target: Sharpe ≥ 1.25, Fitness ≥ 1.0, Turnover 10–70%, TOP3000|Subindustry|3|0.08.
NEVER use ts_max, ts_min, or delay.

Complete the full cycle in this session.
"""


def _write_status(state: str, task: str, cycle: int, extra: dict = None):
    DATA_DIR.mkdir(exist_ok=True)
    payload = {
        "agent_state": state,
        "status": state,
        "current_task": task,
        "current_cycle": cycle,
        "last_updated": datetime.now(UTC).isoformat(),
        **(extra or {}),
    }
    STATUS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("Status → %s | task=%s | cycle=%d", state, task, cycle)


def _read_cycle() -> int:
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text())["current_cycle"]
        except Exception:
            pass
    return 0


def _deerflow_url() -> str:
    url = os.getenv("DEERFLOW_URL", "http://localhost:8000")
    return url.rstrip("/")


def run_cycle(dry_run: bool = False) -> bool:
    cycle = _read_cycle() + 1
    base = _deerflow_url()

    if dry_run:
        log.info("DRY RUN — would POST to %s/api/chat/stream (cycle %d)", base, cycle)
        log.info("Prompt length: %d chars", len(RESEARCH_PROMPT))
        return True

    # Check DeerFlow is reachable
    try:
        r = requests.get(f"{base}/api/models", timeout=10)
        r.raise_for_status()
        log.info("DeerFlow reachable at %s", base)
    except Exception as e:
        log.error("DeerFlow not reachable at %s: %s", base, e)
        _write_status("error", f"DeerFlow unreachable: {e}", cycle - 1)
        return False

    _write_status("running", "Initialising research cycle", cycle)

    thread_id = f"alpha-cycle-{cycle}-{int(time.time())}"
    payload = {
        "messages": [{"role": "user", "content": RESEARCH_PROMPT.strip()}],
        "thread_id": thread_id,
    }

    log.info("Starting cycle %d (thread=%s)", cycle, thread_id)
    _write_status("running", "DeerFlow researching…", cycle, {"thread_id": thread_id})

    try:
        with requests.post(
            f"{base}/api/chat/stream",
            json=payload,
            stream=True,
            timeout=1800,  # 30 min max per cycle
        ) as resp:
            resp.raise_for_status()
            tool_calls = []
            last_event = ""
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                if line.startswith("data:"):
                    try:
                        data = json.loads(line[5:].strip())
                        event_type = data.get("type", "")
                        if event_type == "tool_call":
                            tool_name = data.get("name", "unknown")
                            tool_calls.append(tool_name)
                            _write_status("running", f"Tool: {tool_name}", cycle,
                                          {"thread_id": thread_id, "tools_used": tool_calls})
                            log.info("Tool call: %s", tool_name)
                        elif event_type == "message" and data.get("role") == "assistant":
                            last_event = data.get("content", "")[:120]
                    except json.JSONDecodeError:
                        pass

        _write_status("idle", "Cycle complete", cycle, {
            "thread_id": thread_id,
            "tools_used": tool_calls,
            "last_message": last_event,
        })
        log.info("Cycle %d complete. Tools used: %s", cycle, tool_calls)
        return True

    except Exception as e:
        log.error("Cycle %d failed: %s", cycle, e)
        _write_status("error", f"Cycle failed: {e}", cycle)
        return False


def main():
    parser = argparse.ArgumentParser(description="Alpha research cycle runner")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without calling DeerFlow")
    args = parser.parse_args()

    # Load .env if present
    env_file = ROOT / "operation" / "deerflow" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    success = run_cycle(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
