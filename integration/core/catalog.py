"""catalog — discover bound loops and their latest run status.

Scans a root for distilled skills (`*/SKILL.md`), reports for each: the skill id,
whether a `loop.md` and receipt exist, distill provenance (from `meta.json`), and
the most recent run result (from the governance audit trail). Computed on demand —
no separate database to keep in sync.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .skill_to_loop import parse_skill


@dataclass
class CatalogEntry:
    id: str
    title: str
    skill_path: str
    has_loop: bool
    has_receipt: bool
    model: str
    domain: str
    last_result: str | None = None
    last_run_ts: str | None = None
    red_lines: int = 0
    milestones: int = 0


def _latest_run(events: list[dict], loop_title: str) -> tuple[str | None, str | None]:
    latest = None
    for ev in events:
        if ev.get("kind") == "run.finished" and ev.get("subject") in (loop_title, f"{loop_title} Loop"):
            latest = ev
    if not latest:
        return None, None
    return latest.get("detail", {}).get("result"), latest.get("ts")


def build_catalog(root: str | Path = "examples") -> list[CatalogEntry]:
    root = Path(root)
    try:
        from ..governance.audit import read_events
        events = read_events()
    except Exception:  # noqa: BLE001
        events = []

    entries: list[CatalogEntry] = []
    for skill_md in sorted(root.glob("*/SKILL.md")):
        try:
            skill = parse_skill(skill_md)
        except Exception:  # noqa: BLE001
            continue
        d = skill_md.parent
        result, ts = _latest_run(events, skill.title)
        entries.append(CatalogEntry(
            id=skill.id,
            title=skill.title,
            skill_path=str(skill_md),
            has_loop=(d / "loop.md").exists(),
            has_receipt=(d / "RECEIPT.md").exists() or (d / "RECEIPT.live.md").exists(),
            model=skill.metadata.get("model", "unknown"),
            domain=(skill.metadata.get("domains", [""]) or [""])[0],
            last_result=result,
            last_run_ts=ts,
            red_lines=len(skill.red_lines),
            milestones=len(skill.milestones),
        ))
    return entries


def to_dicts(entries: list[CatalogEntry]) -> list[dict]:
    return [e.__dict__ for e in entries]


def render_table(entries: list[CatalogEntry]) -> str:
    if not entries:
        return "(no skills found — distill one with forge/harness, then bind it)"
    rows = ["ID                                          LOOP  RECEIPT  LAST RESULT       MODEL",
            "-" * 92]
    for e in entries:
        rows.append(
            f"{e.id:<43} {'yes' if e.has_loop else ' no':>4}  "
            f"{'yes' if e.has_receipt else 'no':>7}  {(e.last_result or '—'):<16}  {e.model}"
        )
    return "\n".join(rows)
