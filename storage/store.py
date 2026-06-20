# storage/store.py — Unified SQLite DAO for the v2 architecture.
#
# One thin data-access object wrapping a single SQLite database
# (data/alpha_store.db). Used by crawlers, the pipeline, the WQB client and
# the retriever. CRUD only — no business logic lives here.
#
# See design.md §3.2 for the schema.
import json
import sqlite3
import time
from pathlib import Path
from typing import Iterable, Optional

import sys
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import STORE_DB


_SCHEMA = """
-- ── Crawled WQB metadata ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS datasets (
    id              TEXT,
    name            TEXT,
    region          TEXT,
    universe        TEXT,
    delay           INTEGER,
    instrument_type TEXT,
    field_count     INTEGER,
    raw             TEXT,
    crawled_at      TEXT,
    PRIMARY KEY (id, region, universe, delay)
);

CREATE TABLE IF NOT EXISTS datafields (
    id          TEXT,
    dataset_id  TEXT,
    region      TEXT,
    universe    TEXT,
    delay       INTEGER,
    type        TEXT,
    description TEXT,
    coverage    REAL,
    user_count  INTEGER,
    raw         TEXT,
    crawled_at  TEXT,
    PRIMARY KEY (id, region, universe, delay)
);
CREATE INDEX IF NOT EXISTS ix_datafields_dataset ON datafields (dataset_id);
CREATE INDEX IF NOT EXISTS ix_datafields_type    ON datafields (type);

CREATE TABLE IF NOT EXISTS operators (
    name       TEXT PRIMARY KEY,
    category   TEXT,
    scope      TEXT,
    definition TEXT,
    raw        TEXT,
    crawled_at TEXT
);

-- ── RAG corpus ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id            TEXT PRIMARY KEY,
    source        TEXT,
    source_type   TEXT,
    category      TEXT,
    quality_score INTEGER,
    ingested_at   TEXT,
    raw_path      TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id            TEXT PRIMARY KEY,
    document_id   TEXT,
    content       TEXT,
    category      TEXT,
    quality_score INTEGER,
    word_count    INTEGER,
    chunk_type    TEXT
);
CREATE INDEX IF NOT EXISTS ix_chunks_document ON chunks (document_id);
CREATE INDEX IF NOT EXISTS ix_chunks_category ON chunks (category);

CREATE TABLE IF NOT EXISTS chunk_vectors (
    chunk_id TEXT PRIMARY KEY,
    model    TEXT,
    dim      INTEGER,
    vector   BLOB
);

-- ── Run history ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS simulations (
    sim_id   TEXT PRIMARY KEY,
    formula  TEXT,
    settings TEXT,
    status   TEXT,
    raw      TEXT,
    ts       TEXT
);

CREATE TABLE IF NOT EXISTS alpha_results (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    formula  TEXT,
    settings TEXT,
    sharpe   REAL,
    fitness  REAL,
    turnover REAL,
    returns  REAL,
    margin   REAL,
    drawdown REAL,
    ts       TEXT,
    full     TEXT
);

CREATE TABLE IF NOT EXISTS gold_alphas (
    id       TEXT PRIMARY KEY,
    name     TEXT,
    formula  TEXT,
    settings TEXT,
    sharpe   REAL,
    fitness  REAL,
    turnover REAL,
    returns  REAL,
    drawdown REAL,
    margin   REAL,
    status   TEXT
);

CREATE TABLE IF NOT EXISTS failed_alphas (
    formula  TEXT,
    settings TEXT,
    sharpe   REAL,
    fitness  REAL,
    ts       TEXT,
    PRIMARY KEY (formula, settings)
);

-- ── Crawl checkpoints (incremental / resume) ────────────────────────────────
CREATE TABLE IF NOT EXISTS crawl_state (
    key        TEXT PRIMARY KEY,
    cursor     TEXT,
    updated_at TEXT
);

-- ── Source Intelligence ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id                   TEXT PRIMARY KEY,
    url                  TEXT,
    source_domain        TEXT NOT NULL,
    source_type          TEXT NOT NULL,
    title                TEXT,
    crawled_at           TEXT,
    last_checked         TEXT,
    hypotheses_generated INTEGER DEFAULT 0,
    alphas_tested        INTEGER DEFAULT 0,
    alphas_gold          INTEGER DEFAULT 0,
    is_blacklisted       BOOLEAN DEFAULT 0,
    blacklist_reason     TEXT,
    notes                TEXT
);

CREATE TABLE IF NOT EXISTS chunk_sources (
    chunk_id  TEXT,
    source_id TEXT,
    PRIMARY KEY (chunk_id, source_id)
);

CREATE VIEW IF NOT EXISTS source_domain_stats AS
SELECT
    source_domain,
    COUNT(*) as source_count,
    SUM(alphas_tested) as total_tested,
    SUM(alphas_gold) as total_gold,
    ROUND(CAST(SUM(alphas_gold) AS REAL) / NULLIF(SUM(alphas_tested), 0) * 100, 1) as effectiveness_pct
FROM knowledge_sources
WHERE is_blacklisted = 0
GROUP BY source_domain;

CREATE VIEW IF NOT EXISTS source_type_stats AS
SELECT
    source_domain,
    source_type,
    COUNT(*) as source_count,
    SUM(alphas_tested) as total_tested,
    SUM(alphas_gold) as total_gold,
    ROUND(CAST(SUM(alphas_gold) AS REAL) / NULLIF(SUM(alphas_tested), 0) * 100, 1) as effectiveness_pct
FROM knowledge_sources
WHERE is_blacklisted = 0
GROUP BY source_domain, source_type
ORDER BY effectiveness_pct DESC;
"""


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Store:
    """Thin SQLite DAO. Open once, reuse. Thread-unsafe (single-process use)."""

    def __init__(self, db_path: Path = STORE_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.init_schema()

    def init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ── Datasets / datafields / operators ───────────────────────────────────
    def upsert_datasets(self, rows: Iterable[dict]) -> int:
        sql = """
            INSERT INTO datasets (id, name, region, universe, delay,
                                  instrument_type, field_count, raw, crawled_at)
            VALUES (:id, :name, :region, :universe, :delay,
                    :instrument_type, :field_count, :raw, :crawled_at)
            ON CONFLICT(id, region, universe, delay) DO UPDATE SET
                name=excluded.name, field_count=excluded.field_count,
                raw=excluded.raw, crawled_at=excluded.crawled_at
        """
        n = 0
        for ds in rows:
            self.conn.execute(sql, {
                "id": ds.get("id"),
                "name": ds.get("name", ""),
                "region": ds.get("_region"),
                "universe": ds.get("_universe"),
                "delay": ds.get("_delay"),
                "instrument_type": ds.get("_instrument_type", "EQUITY"),
                "field_count": ds.get("fieldCount", ds.get("field_count", 0)),
                "raw": json.dumps(ds, ensure_ascii=False),
                "crawled_at": _now(),
            })
            n += 1
        self.conn.commit()
        return n

    def upsert_datafields(self, rows: Iterable[dict]) -> int:
        sql = """
            INSERT INTO datafields (id, dataset_id, region, universe, delay,
                                    type, description, coverage, user_count,
                                    raw, crawled_at)
            VALUES (:id, :dataset_id, :region, :universe, :delay,
                    :type, :description, :coverage, :user_count,
                    :raw, :crawled_at)
            ON CONFLICT(id, region, universe, delay) DO UPDATE SET
                type=excluded.type, description=excluded.description,
                coverage=excluded.coverage, user_count=excluded.user_count,
                raw=excluded.raw, crawled_at=excluded.crawled_at
        """
        n = 0
        for f in rows:
            ds = f.get("dataset", {}) or {}
            self.conn.execute(sql, {
                "id": f.get("id"),
                "dataset_id": ds.get("id") or f.get("_dataset_id", ""),
                "region": f.get("_region"),
                "universe": f.get("_universe"),
                "delay": f.get("_delay"),
                "type": f.get("type", ""),
                "description": f.get("description", ""),
                "coverage": f.get("coverage", 0) or 0,
                "user_count": f.get("userCount", 0) or 0,
                "raw": json.dumps(f, ensure_ascii=False),
                "crawled_at": _now(),
            })
            n += 1
        self.conn.commit()
        return n

    def upsert_operators(self, rows: Iterable[dict]) -> int:
        sql = """
            INSERT INTO operators (name, category, scope, definition, raw, crawled_at)
            VALUES (:name, :category, :scope, :definition, :raw, :crawled_at)
            ON CONFLICT(name) DO UPDATE SET
                category=excluded.category, scope=excluded.scope,
                definition=excluded.definition, raw=excluded.raw,
                crawled_at=excluded.crawled_at
        """
        n = 0
        for op in rows:
            scope = op.get("scope", "")
            if isinstance(scope, list):
                scope = ",".join(scope)
            self.conn.execute(sql, {
                "name": op.get("name"),
                "category": op.get("category", ""),
                "scope": scope,
                "definition": op.get("definition", op.get("description", "")),
                "raw": json.dumps(op, ensure_ascii=False),
                "crawled_at": _now(),
            })
            n += 1
        self.conn.commit()
        return n

    def query_datafields(self, region: str = None, universe: str = None,
                         delay: int = None, type: str = None,
                         search: str = None, limit: int = 50) -> list:
        clauses, params = [], []
        if region:   clauses.append("region = ?");   params.append(region)
        if universe: clauses.append("universe = ?"); params.append(universe)
        if delay is not None: clauses.append("delay = ?"); params.append(delay)
        if type:     clauses.append("type = ?");     params.append(type)
        if search:
            clauses.append("(id LIKE ? OR description LIKE ?)")
            params += [f"%{search}%", f"%{search}%"]
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM datafields{where} ORDER BY coverage DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def list_operators(self, category: str = None) -> list:
        if category:
            rows = self.conn.execute(
                "SELECT * FROM operators WHERE category = ? ORDER BY name", (category,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM operators ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    def operator_names(self) -> set:
        return {r[0] for r in self.conn.execute("SELECT name FROM operators").fetchall()}

    # ── Crawl checkpoints ───────────────────────────────────────────────────
    def set_crawl_state(self, key: str, cursor: dict) -> None:
        self.conn.execute("""
            INSERT INTO crawl_state (key, cursor, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET cursor=excluded.cursor,
                                           updated_at=excluded.updated_at
        """, (key, json.dumps(cursor), _now()))
        self.conn.commit()

    def get_crawl_state(self, key: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT cursor FROM crawl_state WHERE key = ?", (key,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def clear_crawl_state(self, key: str) -> None:
        self.conn.execute("DELETE FROM crawl_state WHERE key = ?", (key,))
        self.conn.commit()

    # ── RAG corpus ──────────────────────────────────────────────────────────
    def upsert_document(self, doc: dict) -> None:
        self.conn.execute("""
            INSERT INTO documents (id, source, source_type, category,
                                   quality_score, ingested_at, raw_path)
            VALUES (:id, :source, :source_type, :category,
                    :quality_score, :ingested_at, :raw_path)
            ON CONFLICT(id) DO UPDATE SET
                source=excluded.source, source_type=excluded.source_type,
                category=excluded.category, quality_score=excluded.quality_score,
                ingested_at=excluded.ingested_at, raw_path=excluded.raw_path
        """, {
            "id": doc["id"], "source": doc.get("source", ""),
            "source_type": doc.get("source_type", ""),
            "category": doc.get("category", ""),
            "quality_score": doc.get("quality_score", 0),
            "ingested_at": doc.get("ingested_at", _now()),
            "raw_path": doc.get("raw_path", ""),
        })
        self.conn.commit()

    def replace_chunks(self, document_id: str, chunks: list) -> int:
        """Idempotent: delete existing chunks for a doc, insert fresh ones."""
        self.conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        sql = """
            INSERT OR REPLACE INTO chunks
                (id, document_id, content, category, quality_score, word_count, chunk_type)
            VALUES (:id, :document_id, :content, :category, :quality_score,
                    :word_count, :chunk_type)
        """
        for c in chunks:
            self.conn.execute(sql, c)
        self.conn.commit()
        return len(chunks)

    def all_chunks(self) -> list:
        return [dict(r) for r in self.conn.execute("SELECT * FROM chunks").fetchall()]

    def chunks_missing_vectors(self) -> list:
        rows = self.conn.execute("""
            SELECT c.* FROM chunks c
            LEFT JOIN chunk_vectors v ON v.chunk_id = c.id
            WHERE v.chunk_id IS NULL
        """).fetchall()
        return [dict(r) for r in rows]

    def upsert_chunk_vector(self, chunk_id: str, model: str, dim: int, vector: bytes) -> None:
        self.conn.execute("""
            INSERT INTO chunk_vectors (chunk_id, model, dim, vector) VALUES (?, ?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                model=excluded.model, dim=excluded.dim, vector=excluded.vector
        """, (chunk_id, model, dim, vector))
        self.conn.commit()

    def get_chunk_vectors(self) -> dict:
        """Return {chunk_id: (model, dim, vector_bytes)}."""
        rows = self.conn.execute("SELECT chunk_id, model, dim, vector FROM chunk_vectors").fetchall()
        return {r[0]: (r[1], r[2], r[3]) for r in rows}

    def count(self, table: str) -> int:
        return self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    # ── Run history ─────────────────────────────────────────────────────────
    def save_simulation(self, sim_id: str, formula: str, settings: str,
                        status: str, raw: dict) -> None:
        self.conn.execute("""
            INSERT OR IGNORE INTO simulations (sim_id, formula, settings, status, raw, ts)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sim_id, formula, settings, status, json.dumps(raw), _now()))
        self.conn.commit()

    def save_alpha_result(self, m: dict) -> None:
        self.conn.execute("""
            INSERT INTO alpha_results (formula, settings, sharpe, fitness, turnover,
                                       returns, margin, drawdown, ts, full)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m.get("formula", ""), m.get("settings", ""), m.get("sharpe", 0.0),
            m.get("fitness", 0.0), m.get("turnover", 0.0), m.get("returns", 0.0),
            m.get("margin", 0.0), m.get("drawdown", 0.0), _now(),
            json.dumps({k: v for k, v in m.items() if k != "raw_api_response"}),
        ))
        self.conn.commit()

    def upsert_gold_alpha(self, m: dict) -> None:
        self.conn.execute("""
            INSERT INTO gold_alphas (id, name, formula, settings, sharpe, fitness,
                                     turnover, returns, drawdown, margin, status)
            VALUES (:id, :name, :formula, :settings, :sharpe, :fitness,
                    :turnover, :returns, :drawdown, :margin, :status)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, status=excluded.status
        """, {
            "id": m.get("id"), "name": m.get("name", "Untitled Alpha"),
            "formula": m.get("formula"), "settings": m.get("settings"),
            "sharpe": m.get("sharpe"), "fitness": m.get("fitness"),
            "turnover": m.get("turnover"), "returns": m.get("returns"),
            "drawdown": m.get("drawdown"), "margin": m.get("margin"),
            "status": m.get("status", "UNSUBMITTED"),
        })
        self.conn.commit()

    def get_gold_alphas(self) -> list:
        return [dict(r) for r in self.conn.execute("SELECT * FROM gold_alphas").fetchall()]

    def is_failed(self, formula: str, settings: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM failed_alphas WHERE formula = ? AND settings = ?",
            (formula.strip(), settings),
        ).fetchone()
        return row is not None

    def save_failed(self, formula: str, settings: str, sharpe: float, fitness: float) -> None:
        self.conn.execute("""
            INSERT OR IGNORE INTO failed_alphas (formula, settings, sharpe, fitness, ts)
            VALUES (?, ?, ?, ?, ?)
        """, (formula.strip(), settings, sharpe, fitness, _now()))
        self.conn.commit()


    # ── Source Intelligence ─────────────────────────────────────────────────
    def register_source(self, sid: str, url: str, source_domain: str,
                        source_type: str, title: str = "", notes: str = "") -> None:
        self.conn.execute("""
            INSERT INTO knowledge_sources
                (id, url, source_domain, source_type, title, crawled_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                last_checked=excluded.crawled_at,
                title=COALESCE(excluded.title, title)
        """, (sid, url, source_domain, source_type, title, _now(), notes))
        self.conn.commit()

    def record_source_alpha(self, source_id: str, status: str) -> None:
        """status: 'gold' | 'failed' | 'correlated'"""
        self.conn.execute("""
            UPDATE knowledge_sources
            SET alphas_tested = alphas_tested + 1,
                alphas_gold   = alphas_gold + ?,
                last_checked  = ?
            WHERE id = ?
        """, (1 if status == "gold" else 0, _now(), source_id))
        self.conn.commit()

    def get_source(self, source_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM knowledge_sources WHERE id = ?", (source_id,)
        ).fetchone()
        return dict(row) if row else None

    def source_domain_stats(self) -> list:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM source_domain_stats"
        ).fetchall()]

    def source_type_stats(self) -> list:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM source_type_stats"
        ).fetchall()]

    def priority_sources(self, top_n: int = 5, domain: str = None) -> list:
        where = "WHERE is_blacklisted = 0 AND alphas_tested > 0"
        params = []
        if domain:
            where += " AND source_domain = ?"
            params.append(domain)
        sql = f"""
            SELECT *, ROUND(CAST(alphas_gold AS REAL)/alphas_tested*100, 1) as eff_pct
            FROM knowledge_sources
            {where}
            ORDER BY eff_pct DESC, alphas_gold DESC
            LIMIT ?
        """
        params.append(top_n)
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def blacklist_source(self, source_id: str, reason: str) -> None:
        self.conn.execute("""
            UPDATE knowledge_sources
            SET is_blacklisted = 1, blacklist_reason = ?
            WHERE id = ?
        """, (reason, source_id))
        self.conn.commit()

    def link_chunk_source(self, chunk_id: str, source_id: str) -> None:
        self.conn.execute("""
            INSERT OR IGNORE INTO chunk_sources (chunk_id, source_id) VALUES (?, ?)
        """, (chunk_id, source_id))
        self.conn.commit()

    def all_sources(self, include_blacklisted: bool = False) -> list:
        where = "" if include_blacklisted else "WHERE is_blacklisted = 0"
        return [dict(r) for r in self.conn.execute(
            f"SELECT * FROM knowledge_sources {where} ORDER BY crawled_at DESC"
        ).fetchall()]


if __name__ == "__main__":
    s = Store()
    s.init_schema()
    tables = [r[0] for r in s.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    print("OK — tables:", tables)
