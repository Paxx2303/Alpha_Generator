"""Lightweight web dashboard for Alpha_Generator.

Inspired by the Dify-based UI shipped in the legacy `worldquant-miner`
(`generation_one/agent-dify-web`), but rebuilt as a tiny FastAPI app that
talks directly to `AlphaPipeline.run_once` instead of pulling in the full
Dify stack. Provides:

  * `GET  /`               - HTML control panel
  * `POST /api/generate`   - kick off a single pipeline run (background)
  * `GET  /api/status`     - last run status / metrics
  * `GET  /api/docs-status`- whether the WQ Brain doc corpus is loaded

Run with::

    uvicorn dashboard.web_app:app --reload --port 8765
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from config import load_config
from knowledge_base.wq_docs_rag import WQBrainDocsRAG
from pipeline.alpha_pipeline import AlphaPipeline

LOGGER = logging.getLogger(__name__)


@dataclass
class RunState:
    running: bool = False
    started_at: str | None = None
    finished_at: str | None = None
    strategy_type: str | None = None
    count: int | None = None
    error: str | None = None
    alphas: list[dict[str, Any]] = field(default_factory=list)


_state = RunState()
_state_lock = threading.Lock()
_pipeline_lock = threading.Lock()
_pipeline: AlphaPipeline | None = None


def _get_pipeline() -> AlphaPipeline:
    global _pipeline
    with _pipeline_lock:
        if _pipeline is None:
            _pipeline = AlphaPipeline(load_config())
        return _pipeline


class GenerateRequest(BaseModel):
    strategy_type: str = "momentum"
    count: int = 1
    submit_enabled: bool = False


app = FastAPI(title="Alpha_Generator Dashboard", version="1.0")


INDEX_HTML = """<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\"/>
<title>Alpha_Generator Dashboard</title>
<style>
 body{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:880px;margin:32px auto;padding:0 20px;color:#1f2937}
 h1{margin-bottom:4px}
 .card{border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin:14px 0;background:#fafafa}
 label{display:block;margin:6px 0 4px;font-size:14px;color:#374151}
 input,select,button{font-size:14px;padding:6px 10px;border-radius:6px;border:1px solid #d1d5db}
 button{background:#2563eb;color:#fff;border-color:#2563eb;cursor:pointer}
 button:disabled{background:#9ca3af;border-color:#9ca3af;cursor:not-allowed}
 pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;overflow-x:auto;font-size:12.5px}
 .row{display:flex;gap:12px;flex-wrap:wrap;align-items:end}
 .pill{display:inline-block;padding:2px 8px;border-radius:999px;background:#e5e7eb;font-size:12px}
 .ok{background:#dcfce7;color:#166534}
 .warn{background:#fef3c7;color:#92400e}
 .err{background:#fee2e2;color:#991b1b}
</style>
</head>
<body>
<h1>Alpha_Generator Dashboard</h1>
<div class=\"card\" id=\"docs\">Loading WQ Brain docs status...</div>

<div class=\"card\">
 <div class=\"row\">
  <div><label>Strategy</label>
   <select id=\"strategy\">
    <option>momentum</option><option>mean_reversion</option>
    <option>volume_breakout</option><option>volatility</option>
   </select></div>
  <div><label>Count</label><input id=\"count\" type=\"number\" value=\"1\" min=\"1\" max=\"10\"/></div>
  <div><label><input id=\"submit\" type=\"checkbox\"/> Auto-submit if passing</label></div>
  <div><button id=\"go\">Generate</button></div>
 </div>
</div>

<div class=\"card\"><b>Status:</b> <span id=\"status\" class=\"pill\">idle</span>
 <div id=\"meta\" style=\"margin-top:8px;font-size:13px;color:#4b5563\"></div></div>
<div class=\"card\"><b>Alphas</b><pre id=\"alphas\">(none yet)</pre></div>

<script>
async function refreshDocs(){
 const r = await fetch('/api/docs-status'); const j = await r.json();
 const el = document.getElementById('docs');
 if(j.empty){el.innerHTML = '<span class=\"pill warn\">WQ Brain docs empty</span> &nbsp; Drop files into <code>docs/wq_brain/</code> and restart.';}
 else {el.innerHTML = '<span class=\"pill ok\">WQ Brain docs indexed</span> &nbsp; Hermes prompts now grounded in official documentation.';}
}
async function refreshStatus(){
 const r = await fetch('/api/status'); const j = await r.json();
 const s = document.getElementById('status');
 s.className = 'pill ' + (j.running ? 'warn' : (j.error ? 'err' : 'ok'));
 s.textContent = j.running ? 'running' : (j.error ? 'error' : (j.finished_at ? 'done' : 'idle'));
 document.getElementById('meta').textContent =
   `strategy=${j.strategy_type||'-'} count=${j.count||'-'} started=${j.started_at||'-'} finished=${j.finished_at||'-'}` + (j.error?` err=${j.error}`:'');
 document.getElementById('alphas').textContent = j.alphas.length ? JSON.stringify(j.alphas, null, 2) : '(none yet)';
 document.getElementById('go').disabled = j.running;
}
document.getElementById('go').onclick = async () => {
 const body = {strategy_type:strategy.value, count:parseInt(count.value)||1, submit_enabled:submit.checked};
 await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 refreshStatus();
};
refreshDocs(); refreshStatus(); setInterval(refreshStatus, 4000);
</script>
</body></html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/api/docs-status")
def docs_status() -> dict[str, Any]:
    rag = WQBrainDocsRAG.shared()
    rag.load()
    docs_count = sum(len(kb.documents) for kb in rag._kbs)  # noqa: SLF001
    return {"empty": rag.is_empty, "chunks": docs_count, "root": str(rag.root)}


@app.get("/api/status")
def status() -> dict[str, Any]:
    with _state_lock:
        return {
            "running": _state.running,
            "started_at": _state.started_at,
            "finished_at": _state.finished_at,
            "strategy_type": _state.strategy_type,
            "count": _state.count,
            "error": _state.error,
            "alphas": _state.alphas,
        }


def _run_pipeline_thread(req: GenerateRequest) -> None:
    pipeline = _get_pipeline()
    try:
        results = pipeline.run_once(
            strategy_type=req.strategy_type,
            count=req.count,
            submit_enabled=req.submit_enabled,
        )
        alphas: list[dict[str, Any]] = []
        for ev in results or []:
            metrics = getattr(ev, "metrics", None)
            cand = getattr(ev, "candidate", None) or getattr(ev, "alpha", None)
            alphas.append(
                {
                    "expression": getattr(cand, "expression", str(cand)) if cand else "",
                    "strategy_type": getattr(cand, "strategy_type", None) if cand else None,
                    "sharpe": getattr(metrics, "sharpe", None) if metrics else None,
                    "fitness": getattr(metrics, "fitness", None) if metrics else None,
                    "turnover": getattr(metrics, "turnover", None) if metrics else None,
                    "returns": getattr(metrics, "returns", None) if metrics else None,
                    "drawdown": getattr(metrics, "drawdown", None) if metrics else None,
                    "self_correlation": getattr(metrics, "self_correlation", None) if metrics else None,
                }
            )
        with _state_lock:
            _state.alphas = alphas
            _state.error = None
    except Exception as exc:  # pragma: no cover - surfaced via UI
        LOGGER.exception("Pipeline run failed")
        with _state_lock:
            _state.error = f"{type(exc).__name__}: {exc}"
    finally:
        with _state_lock:
            _state.running = False
            _state.finished_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"


@app.post("/api/generate")
def generate(req: GenerateRequest) -> dict[str, Any]:
    with _state_lock:
        if _state.running:
            raise HTTPException(status_code=409, detail="A pipeline run is already in progress.")
        _state.running = True
        _state.started_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        _state.finished_at = None
        _state.strategy_type = req.strategy_type
        _state.count = req.count
        _state.error = None
        _state.alphas = []
    threading.Thread(target=_run_pipeline_thread, args=(req,), daemon=True).start()
    return {"started": True}
