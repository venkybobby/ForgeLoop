"""runs — persistent run records with a pending → approved lifecycle (SQLite).

Backs the web app's approval workflow and per-user scoping: each run has an
`owner`, a `pending-approval → running → done` status, and stores its receipt.
Public API (create / get / list_runs / finish) is unchanged except for the new
`owner` field and an optional `owner=` filter on `list_runs`.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from . import db

PENDING = "pending-approval"
RUNNING = "running"
DONE = "done"

_COLS = ("run_id", "owner", "loop_id", "loop_path", "skill_path", "trace_path",
         "mode", "status", "created_ts", "base_url", "approved_ts", "result",
         "receipt_md", "receipt")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class RunRecord:
    run_id: str
    loop_id: str
    loop_path: str
    skill_path: str
    trace_path: str
    mode: str
    status: str
    created_ts: str
    owner: str = "local"
    base_url: str | None = None
    approved_ts: str | None = None
    result: str | None = None
    receipt_md: str | None = None
    receipt: dict | None = None

    def save(self) -> "RunRecord":
        db.execute(
            f"INSERT OR REPLACE INTO runs ({','.join(_COLS)}) "
            f"VALUES ({','.join('?' * len(_COLS))})",
            (self.run_id, self.owner, self.loop_id, self.loop_path, self.skill_path,
             self.trace_path, self.mode, self.status, self.created_ts, self.base_url,
             self.approved_ts, self.result, self.receipt_md,
             json.dumps(self.receipt, ensure_ascii=False) if self.receipt else None),
        )
        return self


def _from_row(r) -> RunRecord:
    return RunRecord(
        run_id=r["run_id"], owner=r["owner"], loop_id=r["loop_id"],
        loop_path=r["loop_path"], skill_path=r["skill_path"], trace_path=r["trace_path"],
        mode=r["mode"], status=r["status"], created_ts=r["created_ts"],
        base_url=r["base_url"], approved_ts=r["approved_ts"], result=r["result"],
        receipt_md=r["receipt_md"],
        receipt=json.loads(r["receipt"]) if r["receipt"] else None,
    )


def create(*, loop_id: str, loop_path: str, skill_path: str, trace_path: str,
           mode: str, owner: str = "local", base_url: str | None = None,
           status: str = PENDING) -> RunRecord:
    return RunRecord(
        run_id=new_id(), owner=owner, loop_id=loop_id, loop_path=loop_path,
        skill_path=skill_path, trace_path=trace_path, mode=mode, status=status,
        created_ts=_now(), base_url=base_url,
    ).save()


def get(run_id: str) -> RunRecord | None:
    rows = db.query("SELECT * FROM runs WHERE run_id = ?", (run_id,))
    return _from_row(rows[0]) if rows else None


def list_runs(owner: str | None = None) -> list[RunRecord]:
    if owner is None:
        rows = db.query("SELECT * FROM runs ORDER BY created_ts DESC")
    else:
        rows = db.query("SELECT * FROM runs WHERE owner = ? ORDER BY created_ts DESC", (owner,))
    return [_from_row(r) for r in rows]


def finish(rec: RunRecord, receipt) -> RunRecord:
    rec.status = DONE
    rec.result = receipt.result
    rec.receipt_md = receipt.render()
    rec.receipt = receipt.to_dict()
    return rec.save()
