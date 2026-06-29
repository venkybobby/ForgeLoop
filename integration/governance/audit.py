"""audit — append-only governance trail (SQLite-backed).

Same `AuditEvent` shape as before — { ts, actor, kind, subject, detail } — now
persisted to the SQLite store (`db.py`) instead of a JSONL file, so it survives
restarts and concurrent writers. Public API (`record_event`, `read_events`) is
unchanged, so every caller keeps working.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from . import db

VALID_KINDS = {
    "skill.registered",
    "loop.created",
    "approval.requested",
    "approval.granted",
    "run.started",
    "run.finished",
    "auth.login",
    "auth.logout",
    "ratelimit.blocked",
}


def record_event(*, actor: str, kind: str, subject: str,
                 detail: dict | None = None, ts: str | None = None) -> dict:
    detail = detail or {}
    if kind not in VALID_KINDS:
        detail = {**detail, "_unrecognized_kind": True}
    event = {
        "ts": ts or datetime.now(timezone.utc).isoformat(),
        "actor": actor, "kind": kind, "subject": subject, "detail": detail,
    }
    db.execute(
        "INSERT INTO audit (ts, actor, kind, subject, detail) VALUES (?, ?, ?, ?, ?)",
        (event["ts"], actor, kind, subject, json.dumps(detail, ensure_ascii=False)),
    )
    return event


def read_events(subject: str | None = None) -> list[dict]:
    if subject is None:
        rows = db.query("SELECT * FROM audit ORDER BY id")
    else:
        rows = db.query("SELECT * FROM audit WHERE subject = ? ORDER BY id", (subject,))
    return [
        {"ts": r["ts"], "actor": r["actor"], "kind": r["kind"],
         "subject": r["subject"], "detail": json.loads(r["detail"] or "{}")}
        for r in rows
    ]
