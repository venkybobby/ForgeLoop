"""db — SQLite storage for ForgeLoop governance (audit trail + run records).

Replaces the JSON-file store so the web app survives restarts and supports
concurrent users. Stdlib `sqlite3` only — no external database, no extra deps.
One shared connection guarded by a lock (the web server is multi-threaded);
WAL mode keeps reads/writes from blocking each other.

Path: $FORGELOOP_DB (default ./.data/forgeloop.db, gitignored).
"""

from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path

_LOCK = threading.Lock()
_CONN: sqlite3.Connection | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  ts      TEXT, actor TEXT, kind TEXT, subject TEXT, detail TEXT
);
CREATE TABLE IF NOT EXISTS runs (
  run_id      TEXT PRIMARY KEY,
  owner       TEXT, loop_id TEXT, loop_path TEXT, skill_path TEXT, trace_path TEXT,
  mode        TEXT, status TEXT, created_ts TEXT, base_url TEXT, approved_ts TEXT,
  result      TEXT, receipt_md TEXT, receipt TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_owner ON runs(owner);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_ts);
CREATE INDEX IF NOT EXISTS idx_audit_subject ON audit(subject);
"""


def db_path() -> Path:
    return Path(os.environ.get("FORGELOOP_DB", "./.data/forgeloop.db"))


def _connect() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        p = db_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        _CONN = sqlite3.connect(str(p), check_same_thread=False)
        _CONN.row_factory = sqlite3.Row
        _CONN.execute("PRAGMA journal_mode=WAL")
        _CONN.executescript(_SCHEMA)
        _CONN.commit()
    return _CONN


def execute(sql: str, params: tuple = ()) -> None:
    with _LOCK:
        c = _connect()
        c.execute(sql, params)
        c.commit()


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with _LOCK:
        c = _connect()
        return c.execute(sql, params).fetchall()


def reset_for_tests() -> None:
    """Drop the cached connection (e.g. after changing $FORGELOOP_DB in a test)."""
    global _CONN
    with _LOCK:
        if _CONN is not None:
            _CONN.close()
            _CONN = None
