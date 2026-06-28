"""audit — append-only governance trail for ForgeLoop.

Implements the `AuditEvent` shape from `integration/governance/README.md`:

    AuditEvent { ts, actor, kind, subject, detail }

Events are appended as JSON lines to `GOVERNANCE_AUDIT_DIR/audit.jsonl`
(default `./.data/audit/`, gitignored). Append-only: we never rewrite history.

`ts` is supplied by the caller when known; if omitted we stamp UTC now. The
recorder is deliberately tiny and dependency-free so any module (and the CLI)
can call it without a service running.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

VALID_KINDS = {
    "skill.registered",
    "loop.created",
    "approval.requested",
    "approval.granted",
    "run.started",
    "run.finished",
}


def audit_dir() -> Path:
    return Path(os.environ.get("GOVERNANCE_AUDIT_DIR", "./.data/audit"))


def audit_log_path() -> Path:
    return audit_dir() / "audit.jsonl"


def record_event(
    *,
    actor: str,
    kind: str,
    subject: str,
    detail: dict | None = None,
    ts: str | None = None,
) -> dict:
    """Append one AuditEvent and return it. Unknown kinds are allowed but flagged
    so the trail stays honest rather than silently dropping events."""
    event = {
        "ts": ts or datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "kind": kind,
        "subject": subject,
        "detail": detail or {},
    }
    if kind not in VALID_KINDS:
        event["detail"] = {**event["detail"], "_unrecognized_kind": True}

    path = audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def read_events(subject: str | None = None) -> list[dict]:
    """Read the audit trail, optionally filtered by subject (e.g. a loop/skill id)."""
    path = audit_log_path()
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if subject is None or ev.get("subject") == subject:
            events.append(ev)
    return events
