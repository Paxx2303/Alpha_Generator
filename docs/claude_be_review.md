# Claude BE Review Pack

Updated: 2026-05-18
Scope: Sprint 1 review for backend and persistence changes

## Files changed

- `api_layer/monitor_api.py`
- `database/storage.py`
- `pipeline/submission/quality_gate.py`
- `pipeline/submission/auto_submit.py`
- `pipeline/alpha_pipeline.py`
- `pipeline/brute_force_workflow.py`

## What to review

### TASK-01 Streamlit tab leak

- Added FastAPI redirect for `/_stcore/{path:path}` to `/` with HTTP `301`.
- Root SPA responses now include:
  - `Clear-Site-Data: "cache", "storage"`
  - `Cache-Control: no-store`

Review points:

- Confirm redirect route is registered before SPA fallback catches the request.
- Confirm both `/` and fallback-to-`index.html` responses include the cache-clearing headers.

### TASK-02 Settings partial update and connection test

- `POST /api/settings` now accepts partial payloads via `SettingsPatchPayload`.
- Server merges dirty payload with current config before writing `.env` and YAML files.
- Added `POST /api/settings/test` for `provider=worldquant`.

Review points:

- Confirm unset secret fields do not overwrite stored credentials.
- Confirm `test_settings_connection()` uses current stored credentials when request omits password.

### TASK-03 Quality gate persistence

- `QualityGate.assess()` now returns structured `failures` and `warnings`.
- Pipeline persists `GATE_FAIL` and `GATE_WARNING` events with structured payloads.
- `alpha_runs` migration adds:
  - `gate_failure_reason`
  - `needs_review`
  - `submitted_at`

Review points:

- Confirm `payload.reason`, `payload.field`, `payload.value`, and `payload.threshold` exist on `GATE_FAIL`.
- Confirm `needs_review=True` is set only for borderline pass cases, not hard failures.
- Confirm parsed alpha rows expose `needs_review` as boolean.

### TASK-04 Submit idempotency lock

- `AutoSubmitter` now uses a file-based lock:
  - `.alpha_submit.lock`
- Submission history is recorded in:
  - `.alpha_submit_history.json`
- Duplicate submit attempts are skipped when expression already submitted in DB or history file.

Review points:

- Confirm lock works on Windows without `fcntl`.
- Confirm stale lock cleanup logic does not block future submits after crash.
- Confirm `submitted_at` is attached to successful and pending submit attempts.

## Verification commands

```bash
python -m py_compile main.py api_layer/monitor_api.py
python -m py_compile pipeline/submission/quality_gate.py
python -m py_compile pipeline/submission/auto_submit.py
python -m py_compile pipeline/alpha_pipeline.py
python -m py_compile pipeline/brute_force_workflow.py
python -m py_compile database/storage.py
```

## Smoke tests run locally

```bash
python - <<'PY'
from fastapi.testclient import TestClient
from api_layer.monitor_api import create_app

client = TestClient(create_app())
print(client.get('/_stcore/stream', follow_redirects=False).status_code)
print(client.get('/').headers.get('clear-site-data'))
print(client.post('/api/settings/test', json={'provider': 'worldquant'}).json())
PY
```

Expected:

- `/_stcore/stream` returns `301`
- `/` includes `Clear-Site-Data`
- `/api/settings/test` returns JSON with `status`
