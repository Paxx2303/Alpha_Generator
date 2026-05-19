from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from typing import Any

from pipeline.models import AlphaCandidate, SimulationMetrics


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False)


class AlphaStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alpha_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    expression TEXT NOT NULL,
                    source TEXT NOT NULL,
                    generation_source TEXT,
                    origin_agent TEXT,
                    strategy_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    sharpe REAL,
                    fitness REAL,
                    annual_returns REAL,
                    turnover REAL,
                    drawdown REAL,
                    self_correlation REAL,
                    notes TEXT,
                    rationale TEXT,
                    metadata_json TEXT,
                    checks_json TEXT,
                    agent_reviews_json TEXT,
                    pre_sim_confidence REAL,
                    post_sim_confidence REAL,
                    pre_sim_verdict TEXT,
                    post_sim_verdict TEXT,
                    run_tags_json TEXT,
                    gate_failure_reason TEXT,
                    needs_review INTEGER NOT NULL DEFAULT 0,
                    submitted_at TEXT,
                    pre_backtest_score REAL,
                    pre_backtest_passed INTEGER,
                    pre_backtest_metrics_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    report_date TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_type TEXT NOT NULL,
                    strategy_type TEXT NOT NULL,
                    target_count INTEGER NOT NULL,
                    submit_enabled INTEGER NOT NULL,
                    dry_run INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    current_stage TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    summary_json TEXT,
                    tags_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    level TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    alpha_expression TEXT,
                    alpha_run_id INTEGER,
                    payload_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    query_text TEXT,
                    content TEXT NOT NULL,
                    source_path TEXT,
                    related_alpha_expression TEXT,
                    score REAL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alpha_explanations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alpha_run_id INTEGER NOT NULL UNIQUE,
                    run_id TEXT,
                    theme TEXT NOT NULL,
                    hypothesis TEXT NOT NULL,
                    prompt_context TEXT,
                    expected_metrics_json TEXT,
                    risks_json TEXT,
                    theory_ids_json TEXT,
                    research_refs_json TEXT,
                    field_info_json TEXT,
                    operator_info_json TEXT,
                    agent_reviews_json TEXT,
                    stage_notes_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS theory_entries (
                    theory_id TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    title TEXT NOT NULL,
                    sector_tags_json TEXT NOT NULL,
                    core_principle TEXT NOT NULL,
                    alpha_implication_json TEXT NOT NULL,
                    example_expression TEXT NOT NULL,
                    agent_reasoning_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._migrate(conn)
            conn.commit()

    def _migrate(self, conn: sqlite3.Connection) -> None:
        migrations = {
            "alpha_runs": {
                "run_id": "TEXT",
                "rationale": "TEXT",
                "metadata_json": "TEXT",
                "checks_json": "TEXT",
                "agent_reviews_json": "TEXT",
                "generation_source": "TEXT",
                "origin_agent": "TEXT",
                "pre_sim_confidence": "REAL",
                "post_sim_confidence": "REAL",
                "pre_sim_verdict": "TEXT",
                "post_sim_verdict": "TEXT",
                "run_tags_json": "TEXT",
                "gate_failure_reason": "TEXT",
                "needs_review": "INTEGER NOT NULL DEFAULT 0",
                "submitted_at": "TEXT",
                "pre_backtest_score": "REAL",
                "pre_backtest_passed": "INTEGER",
                "pre_backtest_metrics_json": "TEXT",
            },
            "daily_reports": {
                "run_id": "TEXT",
            },
            "pipeline_runs": {
                "tags_json": "TEXT",
            },
        }
        for table, columns in migrations.items():
            existing = self._column_names(conn, table)
            for name, definition in columns.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    @staticmethod
    def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {str(row["name"]) for row in rows}

    def insert_alpha(
        self,
        candidate: AlphaCandidate,
        metrics: SimulationMetrics,
        status: str,
        notes: str = "",
        run_id: str | None = None,
        rationale: str | None = None,
        metadata: dict[str, Any] | None = None,
        agent_reviews: list[dict[str, Any]] | None = None,
        generation_source: str | None = None,
        origin_agent: str | None = None,
        pre_sim_confidence: float | None = None,
        post_sim_confidence: float | None = None,
        pre_sim_verdict: str | None = None,
        post_sim_verdict: str | None = None,
        run_tags: dict[str, Any] | None = None,
        gate_failure_reason: str | None = None,
        needs_review: bool = False,
        submitted_at: str | None = None,
        pre_backtest_score: float | None = None,
        pre_backtest_passed: bool | None = None,
        pre_backtest_metrics: dict[str, Any] | None = None,
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        payload_metadata = metadata if metadata is not None else dict(candidate.metadata)
        payload_reviews = agent_reviews if agent_reviews is not None else []
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO alpha_runs (
                    run_id, expression, source, strategy_type, status,
                    sharpe, fitness, annual_returns, turnover,
                    drawdown, self_correlation, notes, rationale,
                    metadata_json, checks_json, agent_reviews_json, generation_source,
                    origin_agent, pre_sim_confidence, post_sim_confidence,
                    pre_sim_verdict, post_sim_verdict, run_tags_json,
                    gate_failure_reason, needs_review, submitted_at,
                    pre_backtest_score, pre_backtest_passed, pre_backtest_metrics_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    candidate.expression,
                    candidate.source,
                    candidate.strategy_type,
                    status,
                    metrics.sharpe,
                    metrics.fitness,
                    metrics.annual_returns,
                    metrics.turnover,
                    metrics.drawdown,
                    metrics.self_correlation,
                    notes,
                    rationale or candidate.rationale,
                    _json_dumps(payload_metadata),
                    _json_dumps(metrics.checks),
                    _json_dumps(payload_reviews),
                    generation_source or candidate.source,
                    origin_agent,
                    pre_sim_confidence,
                    post_sim_confidence,
                    pre_sim_verdict,
                    post_sim_verdict,
                    _json_dumps(run_tags or {}),
                    gate_failure_reason,
                    int(needs_review),
                    submitted_at,
                    pre_backtest_score,
                    None if pre_backtest_passed is None else int(pre_backtest_passed),
                    _json_dumps(pre_backtest_metrics or {}),
                    created_at,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_recent(self, limit: int = 25, run_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM alpha_runs"
        params: list[Any] = []
        if run_id:
            query += " WHERE run_id = ?"
            params.append(run_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def get_alpha(self, alpha_run_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM alpha_runs WHERE id = ?", (alpha_run_id,)).fetchone()
        return dict(row) if row else None

    def daily_submission_count(self, day: str | None = None) -> int:
        day = day or datetime.now().strftime("%Y-%m-%d")
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM alpha_runs
                WHERE (status = 'submitted' OR submitted_at IS NOT NULL)
                  AND substr(COALESCE(submitted_at, created_at), 1, 10) = ?
                """,
                (day,),
            ).fetchone()
        return int(row[0] if row else 0)

    def was_expression_submitted(self, expression: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM alpha_runs
                WHERE expression = ?
                  AND (status = 'submitted' OR submitted_at IS NOT NULL)
                LIMIT 1
                """,
                (expression,),
            ).fetchone()
        return row is not None

    def save_daily_report(self, report_date: str, summary: dict[str, Any], run_id: str | None = None) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO daily_reports (run_id, report_date, summary_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, report_date, _json_dumps(summary), created_at),
            )
            conn.commit()

    def latest_report(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT summary_json FROM daily_reports ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def summarize(self) -> dict[str, Any]:
        recent = self.list_recent(limit=100)
        if not recent:
            return {
                "total_runs": 0,
                "approved": 0,
                "submitted": 0,
                "average_sharpe": 0.0,
            }
        average_sharpe = sum((item["sharpe"] or 0.0) for item in recent) / len(recent)
        return {
            "total_runs": len(recent),
            "approved": sum(1 for item in recent if item["status"] == "approved"),
            "submitted": sum(1 for item in recent if item["status"] == "submitted"),
            "average_sharpe": round(average_sharpe, 3),
        }

    def create_pipeline_run(
        self,
        run_id: str,
        workflow_type: str,
        strategy_type: str,
        target_count: int,
        submit_enabled: bool,
        dry_run: bool,
        status: str = "running",
        current_stage: str = "research",
        tags: dict[str, Any] | None = None,
    ) -> None:
        started_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pipeline_runs (
                    run_id, workflow_type, strategy_type, target_count,
                    submit_enabled, dry_run, status, current_stage,
                    started_at, finished_at, summary_json, tags_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT finished_at FROM pipeline_runs WHERE run_id = ?), NULL),
                          COALESCE((SELECT summary_json FROM pipeline_runs WHERE run_id = ?), NULL),
                          COALESCE(?, (SELECT tags_json FROM pipeline_runs WHERE run_id = ?), '{}'))
                """,
                (
                    run_id,
                    workflow_type,
                    strategy_type,
                    target_count,
                    int(submit_enabled),
                    int(dry_run),
                    status,
                    current_stage,
                    started_at,
                    run_id,
                    run_id,
                    _json_dumps(tags or {}),
                    run_id,
                ),
            )
            conn.commit()

    def update_pipeline_run(
        self,
        run_id: str,
        *,
        status: str | None = None,
        current_stage: str | None = None,
        summary: dict[str, Any] | None = None,
    ) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if current_stage is not None:
            updates.append("current_stage = ?")
            params.append(current_stage)
        if summary is not None:
            updates.append("summary_json = ?")
            params.append(_json_dumps(summary))
        if not updates:
            return
        params.append(run_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE pipeline_runs SET {', '.join(updates)} WHERE run_id = ?", tuple(params))
            conn.commit()

    def finish_pipeline_run(self, run_id: str, status: str, summary: dict[str, Any]) -> None:
        finished_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE pipeline_runs
                SET status = ?, current_stage = ?, finished_at = ?, summary_json = ?
                WHERE run_id = ?
                """,
                (status, "store", finished_at, _json_dumps(summary), run_id),
            )
            conn.commit()

    def list_pipeline_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def latest_pipeline_run(self) -> dict[str, Any] | None:
        runs = self.list_pipeline_runs(limit=1)
        return runs[0] if runs else None

    def add_pipeline_event(
        self,
        run_id: str,
        stage: str,
        level: str,
        event_type: str,
        message: str,
        *,
        alpha_expression: str | None = None,
        alpha_run_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO pipeline_events (
                    run_id, stage, level, event_type, message,
                    alpha_expression, alpha_run_id, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    stage,
                    level,
                    event_type,
                    message,
                    alpha_expression,
                    alpha_run_id,
                    _json_dumps(payload or {}),
                    created_at,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_pipeline_events(
        self,
        run_id: str | None = None,
        limit: int = 150,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM pipeline_events"
        params: list[Any] = []
        if run_id:
            query += " WHERE run_id = ?"
            params.append(run_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def save_research_artifact(
        self,
        run_id: str,
        kind: str,
        title: str,
        content: str,
        *,
        query_text: str | None = None,
        source_path: str | None = None,
        related_alpha_expression: str | None = None,
        score: float | None = None,
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO research_artifacts (
                    run_id, kind, title, query_text, content,
                    source_path, related_alpha_expression, score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    kind,
                    title,
                    query_text,
                    content,
                    source_path,
                    related_alpha_expression,
                    score,
                    created_at,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_research_artifacts(self, run_id: str | None = None, limit: int = 40) -> list[dict[str, Any]]:
        query = "SELECT * FROM research_artifacts"
        params: list[Any] = []
        if run_id:
            query += " WHERE run_id = ?"
            params.append(run_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def save_alpha_explanation(
        self,
        alpha_run_id: int,
        run_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO alpha_explanations (
                    alpha_run_id, run_id, theme, hypothesis, prompt_context,
                    expected_metrics_json, risks_json, theory_ids_json,
                    research_refs_json, field_info_json, operator_info_json,
                    agent_reviews_json, stage_notes_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(alpha_run_id) DO UPDATE SET
                    run_id = excluded.run_id,
                    theme = excluded.theme,
                    hypothesis = excluded.hypothesis,
                    prompt_context = excluded.prompt_context,
                    expected_metrics_json = excluded.expected_metrics_json,
                    risks_json = excluded.risks_json,
                    theory_ids_json = excluded.theory_ids_json,
                    research_refs_json = excluded.research_refs_json,
                    field_info_json = excluded.field_info_json,
                    operator_info_json = excluded.operator_info_json,
                    agent_reviews_json = excluded.agent_reviews_json,
                    stage_notes_json = excluded.stage_notes_json
                """,
                (
                    alpha_run_id,
                    run_id,
                    payload.get("theme", ""),
                    payload.get("hypothesis", ""),
                    payload.get("prompt_context", ""),
                    _json_dumps(payload.get("expected_metrics", {})),
                    _json_dumps(payload.get("risks", [])),
                    _json_dumps(payload.get("theory_ids", [])),
                    _json_dumps(payload.get("research_refs", [])),
                    _json_dumps(payload.get("field_info", [])),
                    _json_dumps(payload.get("operator_info", [])),
                    _json_dumps(payload.get("agent_reviews", [])),
                    _json_dumps(payload.get("stage_notes", {})),
                    created_at,
                ),
            )
            conn.commit()

    def get_alpha_explanation(self, alpha_run_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM alpha_explanations WHERE alpha_run_id = ?",
                (alpha_run_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_alpha_explanations(self, run_id: str | None = None, limit: int = 300) -> list[dict[str, Any]]:
        query = "SELECT * FROM alpha_explanations"
        params: list[Any] = []
        if run_id:
            query += " WHERE run_id = ?"
            params.append(run_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def upsert_theory_entry(
        self,
        theory_id: str,
        *,
        domain: str,
        title: str,
        sector_tags: list[str],
        core_principle: str,
        alpha_implication: list[str],
        example_expression: str,
        agent_reasoning: list[str],
        source: str = "catalog_seed",
        status: str = "active",
        created_by: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT version, created_at FROM theory_entries WHERE theory_id = ?",
                (theory_id,),
            ).fetchone()
            version = int(row["version"]) + 1 if row else 1
            created_at = str(row["created_at"]) if row else now
            conn.execute(
                """
                INSERT INTO theory_entries (
                    theory_id, domain, title, sector_tags_json, core_principle,
                    alpha_implication_json, example_expression, agent_reasoning_json,
                    source, status, version, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(theory_id) DO UPDATE SET
                    domain = excluded.domain,
                    title = excluded.title,
                    sector_tags_json = excluded.sector_tags_json,
                    core_principle = excluded.core_principle,
                    alpha_implication_json = excluded.alpha_implication_json,
                    example_expression = excluded.example_expression,
                    agent_reasoning_json = excluded.agent_reasoning_json,
                    source = excluded.source,
                    status = excluded.status,
                    version = excluded.version,
                    created_by = excluded.created_by,
                    updated_at = excluded.updated_at
                """,
                (
                    theory_id,
                    domain,
                    title,
                    _json_dumps(sector_tags),
                    core_principle,
                    _json_dumps(alpha_implication),
                    example_expression,
                    _json_dumps(agent_reasoning),
                    source,
                    status,
                    version,
                    created_by,
                    created_at,
                    now,
                ),
            )
            conn.commit()

    def list_theory_entries(
        self,
        *,
        status: str | None = "active",
        domain: str | None = None,
        search: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM theory_entries"
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if domain:
            clauses.append("domain = ?")
            params.append(domain)
        if search:
            clauses.append(
                "(lower(title) LIKE ? OR lower(core_principle) LIKE ? OR lower(example_expression) LIKE ? OR lower(sector_tags_json) LIKE ?)"
            )
            needle = f"%{search.lower()}%"
            params.extend([needle, needle, needle, needle])
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY domain, title LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def get_theory_entry(self, theory_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM theory_entries WHERE theory_id = ?",
                (theory_id,),
            ).fetchone()
        return dict(row) if row else None

    def sync_theory_catalog(
        self,
        items: list[dict[str, Any]],
        *,
        source: str = "catalog_seed",
        created_by: str | None = "system",
    ) -> int:
        synced = 0
        for item in items:
            self.upsert_theory_entry(
                item["id"],
                domain=item["domain"],
                title=item["title"],
                sector_tags=list(item["sector_tags"]),
                core_principle=item["core_principle"],
                alpha_implication=list(item["alpha_implication"]),
                example_expression=item["example_expression"],
                agent_reasoning=list(item["agent_reasoning"]),
                source=source,
                created_by=created_by,
            )
            synced += 1
        return synced

    def theory_context(
        self,
        query: str,
        *,
        limit: int = 6,
        status: str | None = "active",
    ) -> str:
        rows = self.list_theory_entries(status=status, search=query, limit=limit)
        if not rows:
            rows = self.list_theory_entries(status=status, limit=limit)
        snippets: list[str] = []
        for row in rows:
            try:
                sectors = json.loads(str(row["sector_tags_json"]))
            except json.JSONDecodeError:
                sectors = []
            try:
                implications = json.loads(str(row["alpha_implication_json"]))
            except json.JSONDecodeError:
                implications = []
            try:
                reasoning = json.loads(str(row["agent_reasoning_json"]))
            except json.JSONDecodeError:
                reasoning = []
            snippets.append(
                "\n".join(
                    [
                        f"[theory:{row['theory_id']}] {row['domain']} - {row['title']}",
                        f"Sectors: {', '.join(sectors)}",
                        f"Core principle: {row['core_principle']}",
                        "Alpha implications:",
                        *[f"- {item}" for item in implications],
                        f"Example expression: {row['example_expression']}",
                        "Agent reasoning:",
                        *[f"- {item}" for item in reasoning],
                    ]
                )
            )
        return "\n\n---\n\n".join(snippets)
