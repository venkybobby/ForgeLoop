"""runs — persistent run records with a pending → approved lifecycle.

Backs the web app's approval workflow: a live run is created as **pending**
(awaiting human approval), then `approve()` executes it and stores the receipt.
Records are JSON files under `LOOPY_RUNS_DIR` (default `./.data/runs/`,
gitignored). Stdlib-only; no database.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Lifecycle statuses (distinct from a receipt's terminal *result*).
PENDING = "pending-approval"
RUNNING = "running"
DONE = "done"


def runs_dir() -> Path:
    return Path(os.environ.get("LOOPY_RUNS_DIR", "./.data/runs"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunRecord:
    run_id: str
    loop_id: str
    loop_path: str
    skill_path: str
    trace_path: str
    mode: str                       # "live" | "simulate" | "gate"
    status: str                     # PENDING | RUNNING | DONE
    created_ts: str
    base_url: str | None = None
    approved_ts: str | None = None
    result: str | None = None       # terminal state once finished
    receipt_md: str | None = None
    receipt: dict | None = None

    def path(self) -> Path:
        return runs_dir() / f"{self.run_id}.json"

    def save(self) -> "RunRecord":
        p = self.path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2))
        return self


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def create(*, loop_id: str, loop_path: str, skill_path: str, trace_path: str,
           mode: str, base_url: str | None = None, status: str = PENDING) -> RunRecord:
    rec = RunRecord(
        run_id=new_id(), loop_id=loop_id, loop_path=loop_path, skill_path=skill_path,
        trace_path=trace_path, mode=mode, status=status, created_ts=_now(), base_url=base_url,
    )
    return rec.save()


def get(run_id: str) -> RunRecord | None:
    p = runs_dir() / f"{run_id}.json"
    if not p.exists():
        return None
    return RunRecord(**json.loads(p.read_text()))


def list_runs() -> list[RunRecord]:
    d = runs_dir()
    if not d.exists():
        return []
    out = []
    for p in d.glob("*.json"):
        try:
            out.append(RunRecord(**json.loads(p.read_text())))
        except Exception:  # noqa: BLE001
            continue
    return sorted(out, key=lambda r: r.created_ts, reverse=True)


def finish(rec: RunRecord, receipt) -> RunRecord:
    rec.status = DONE
    rec.result = receipt.result
    rec.receipt_md = receipt.render()
    rec.receipt = receipt.to_dict()
    return rec.save()
