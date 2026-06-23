"""
Shared data-access helpers for the observation dashboard.
Reads from data/alpha_store.db and gold_alphas.json.
"""
import json
import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "alpha_store.db"
GOLD_ALPHAS_PATH = ROOT / "gold_alphas.json"
RESEARCH_LOG_PATH = ROOT / "RESEARCH_LOG.md"
THEORY_LOG_PATH = ROOT / "data" / "theory_log.json"
RESEARCH_STATUS_PATH = ROOT / "data" / "research_status.json"


def _conn():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_gold_alphas() -> pd.DataFrame:
    conn = _conn()
    if conn is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM gold_alphas",
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    if df.empty:
        return df
    if "settings" in df.columns and df["settings"].dtype == object:
        try:
            parts = df["settings"].str.split("|", expand=True)
            if parts.shape[1] >= 4:
                df["universe"] = parts[0]
                df["neutralization"] = parts[1]
                df["decay"] = parts[2].astype(int)
                df["truncation"] = parts[3].astype(float)
        except Exception:
            pass
    if "turnover" in df.columns:
        df["turnover_pct"] = (df["turnover"] * 100).round(1)
    return df


def get_simulations() -> pd.DataFrame:
    conn = _conn()
    if conn is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM simulations ORDER BY ts DESC LIMIT 500",
            conn,
        )
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def get_document_stats() -> dict:
    conn = _conn()
    if conn is None:
        return {}
    try:
        cats = pd.read_sql_query(
            "SELECT category, COUNT(*) as n, AVG(quality_score) as avg_q FROM chunks GROUP BY category ORDER BY n DESC",
            conn,
        )
        total = pd.read_sql_query("SELECT COUNT(*) as n FROM chunks", conn)
        return {
            "by_category": cats.to_dict("records"),
            "total_chunks": int(total["n"].iloc[0]) if not total.empty else 0,
        }
    except Exception:
        return {}
    finally:
        conn.close()


def get_operator_list() -> pd.DataFrame:
    conn = _conn()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(
            "SELECT name, category, scope, definition FROM operators ORDER BY category, name",
            conn,
        )
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def get_research_status() -> dict:
    if RESEARCH_STATUS_PATH.exists():
        with open(RESEARCH_STATUS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {
        "status": "idle",
        "current_cycle": 0,
        "current_task": "Not started",
        "last_updated": None,
        "agent_state": "stopped",
    }


def get_theory_log() -> list:
    if not THEORY_LOG_PATH.exists():
        return []
    with open(THEORY_LOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def append_theory(theory: dict):
    theories = get_theory_log()
    theory.setdefault("created_at", datetime.now(UTC).isoformat())
    theories.append(theory)
    THEORY_LOG_PATH.parent.mkdir(exist_ok=True)
    with open(THEORY_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(theories, f, indent=2, default=str)


def get_research_log() -> str:
    if RESEARCH_LOG_PATH.exists():
        return RESEARCH_LOG_PATH.read_text(encoding="utf-8")
    return "_No RESEARCH_LOG.md found._"


