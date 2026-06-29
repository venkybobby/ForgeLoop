"""skill_to_loop — turn a distilled Forge SKILL.md into a governed Loopy loop.md.

Deterministic, stdlib-only. No LLM call: this is a structural transform that maps
the SKILL.md sections onto the Loopy feedback-cycle conventions documented in
`loopy/skills/loopy/SKILL.md` and `loopy/skills/loopy/references/run.md`:

  Observe -> Choose -> Act -> Verify -> Record -> Repeat or stop

and the named terminal states (Success | Clean no-op | Blocked | Approval
required | Exhausted | No progress).

The produced `loop.md` carries Objective, Success/acceptance criteria, the
feedback cycle, Stopping conditions, Governance (red lines + approval gate), a
compressed Loopy-style Prompt, and a Provenance footer (source path + SHA-256).

CLI:
    python -m integration.core.skill_to_loop <SKILL.md> [--out loop.md]
        [--max-passes N] [--no-audit]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ──────────────────────────── markdown parsing ─────────────────────────────
@dataclass
class Section:
    level: int
    heading: str
    body: list[str] = field(default_factory=list)


def parse_sections(md: str) -> tuple[str, list[Section]]:
    """Return (h1_title, sections). Sections are split on '##' headings; their
    body keeps nested '###'/text/bullets verbatim."""
    title = ""
    sections: list[Section] = []
    current: Section | None = None
    for raw in md.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*\S)\s*$", raw)
        if m and len(m.group(1)) == 1 and not title:
            title = re.sub(r"^skill:\s*", "", m.group(2), flags=re.I).strip()
            continue
        if m and len(m.group(1)) == 2:
            current = Section(level=2, heading=m.group(2).strip())
            sections.append(current)
            continue
        if current is not None:
            current.body.append(raw)
    return title, sections


def find_section(sections: list[Section], *keywords: str) -> Section | None:
    """First section whose heading contains ALL of any keyword group. Each arg is
    a '+'-joined AND group; the first matching group wins."""
    for kw in keywords:
        needles = [n for n in kw.lower().split("+")]
        for s in sections:
            h = s.heading.lower()
            if all(n in h for n in needles):
                return s
    return None


_BULLET = re.compile(r"^\s*(?:[-*]\s+(?:\[[ xX]\]\s+)?|\d+\.\s+)(.*\S)\s*$")
_SUBHEAD = re.compile(r"^\s*#{3,6}\s+(?:\d+\.\s*)?(.*\S)\s*$")


def bullets(section: Section | None, *, limit: int | None = None, max_indent: int = 999) -> list[str]:
    """Bullet/numbered items in a section. `max_indent=1` keeps only top-level
    items (drops nested 'Reason:'/'Correct behavior:' sub-bullets)."""
    if section is None:
        return []
    out: list[str] = []
    for line in section.body:
        m = _BULLET.match(line)
        if m:
            if (len(line) - len(line.lstrip())) > max_indent:
                continue
            text = m.group(1).strip()
            text = re.sub(r"^[✓✗•]\s*", "", text)
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # de-bold
            if text:
                out.append(text)
    return out[:limit] if limit else out


def headed_bullets(md: str, *keywords: str) -> list[str]:
    """Top-level bullets under ANY heading (any level) matching a keyword group —
    used to reach rules nested under H3s (e.g. '### Things You MUST NOT Do') that
    the H2-only section split doesn't expose."""
    out: list[str] = []
    capture = False
    for line in md.splitlines():
        h = re.match(r"^#{1,6}\s+(.*\S)\s*$", line)
        if h:
            head = h.group(1).lower()
            capture = any(all(n in head for n in kw.lower().split("+")) for kw in keywords)
            continue
        if capture:
            m = _BULLET.match(line)
            if m and (len(line) - len(line.lstrip())) <= 1:
                text = re.sub(r"\*\*(.*?)\*\*", r"\1", m.group(1)).strip()
                if text:
                    out.append(text)
    return out


def first_paragraph(section: Section | None) -> str:
    if section is None:
        return ""
    buf: list[str] = []
    for line in section.body:
        if line.strip() == "":
            if buf:
                break
            continue
        if _SUBHEAD.match(line) or _BULLET.match(line):
            if buf:
                break
            continue
        buf.append(line.strip())
    return " ".join(buf).strip()


def subheadings(section: Section | None) -> list[str]:
    if section is None:
        return []
    out = []
    for line in section.body:
        m = _SUBHEAD.match(line)
        if m:
            out.append(re.sub(r"\*\*", "", m.group(1)).strip())
    return out


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "skill"


# ──────────────────────────── data model ───────────────────────────────────
@dataclass
class Skill:
    id: str
    title: str
    source: str
    sha256: str
    objective: str
    trigger: str
    acceptance: list[str]          # observable success / terminal conditions
    milestones: list[str]          # the worklist / checkpoints
    false_terminals: list[str]     # "looks done but isn't" guards
    recovery: list[str]            # what a failed pass learns
    red_lines: list[str]           # never-violate rules (governance)
    security: list[str]            # security boundaries (governance)
    steps: list[str]               # ordered procedure phases
    metadata: dict


def parse_skill(path: str | Path) -> Skill:
    p = Path(path)
    md = p.read_text()
    sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    title, sections = parse_sections(md)

    # sibling meta.json (written by forge/harness) gives domain/capacity/model.
    meta: dict = {}
    meta_path = p.with_name("meta.json")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
        except (json.JSONDecodeError, OSError):
            meta = {}

    domain = meta.get("domains", [None])[0] if meta.get("domains") else p.parent.parent.name
    # Capacity from the skill title (matches the harness bucket name, e.g.
    # "Fill and Submit Form" -> fill-and-submit-form) rather than the folder.
    capacity = slugify(title) if title else (p.parent.name or "skill")
    skill_id = f"{domain}::{capacity}" if domain else capacity

    acceptance = bullets(
        find_section(sections, "terminal condition", "success+criteria", "success+condition", "acceptance"),
        max_indent=1,
    )
    objective = (
        first_paragraph(find_section(sections, "purpose", "overview", "goal"))
        or first_paragraph(sections[0]) if sections else ""
    )
    when_sec = find_section(sections, "when to use", "when+use")
    trigger = first_paragraph(when_sec)
    when_bullets = bullets(when_sec, max_indent=1, limit=2)
    if (not trigger or trigger.rstrip().endswith(":")) and when_bullets:
        lead = trigger.rstrip().rstrip(":")
        trigger = (f"{lead}: " if lead else "") + "; ".join(when_bullets)

    procedure = find_section(sections, "procedure", "step-by-step", "step by step")
    steps = subheadings(procedure) or bullets(procedure, limit=12)

    return Skill(
        id=skill_id,
        title=title or capacity.replace("-", " ").title(),
        source=str(p),
        sha256=sha,
        objective=objective,
        trigger=trigger,
        acceptance=acceptance,
        milestones=bullets(find_section(sections, "milestone"), max_indent=1),
        false_terminals=bullets(find_section(sections, "false terminal"), max_indent=1),
        recovery=subheadings(find_section(sections, "recovery"))
        or bullets(find_section(sections, "recovery", "failure mode"), max_indent=1),
        red_lines=bullets(find_section(sections, "red line"), max_indent=1)
        or headed_bullets(md, "red line", "must not", "never"),
        security=bullets(find_section(sections, "security boundaries", "security"), max_indent=1)
        or headed_bullets(md, "security boundaries", "security boundary"),
        steps=steps,
        metadata=meta,
    )


# ──────────────────────────── loop.md rendering ────────────────────────────
def _md_list(items: list[str], empty: str) -> str:
    return "\n".join(f"- {i}" for i in items) if items else f"- {empty}"


def render_loop_md(skill: Skill, *, max_passes: int | None = None) -> str:
    loop_name = f"{skill.title} Loop"
    model = skill.metadata.get("model", "unknown")
    boundary = (
        f"operator-supplied limit of {max_passes} passes"
        if max_passes
        else "no measurable progress (no-progress stop); operator may set --max-passes"
    )
    objective = skill.objective or f"Perform '{skill.title}' reliably on the target site."
    trigger = skill.trigger or "When the user asks to run this loop on an in-scope target."

    # Compressed Loopy-style prompt (the delivery format from loopy SKILL.md).
    accept_one = skill.acceptance[0] if skill.acceptance else "the observable success condition is met"
    redline_one = skill.red_lines[0] if skill.red_lines else "any irreversible or out-of-scope action"
    prompt = (
        f"{objective} Work in bounded passes: observe the page, take the single "
        f"next in-scope action, then verify against the acceptance check. Keep only "
        f"verified progress. Stop when {accept_one.lower()}, or on no measurable "
        f"progress. Ask before {redline_one.lower()} or any side-effecting browser "
        f"action."
    )

    return f"""\
## {loop_name}

{objective} The loop runs bounded passes and stops at a named terminal state — it
is a feedback system, not permission for unbounded autonomy.

- **Skill id:** `{skill.id}`
- **Source skill:** `{skill.source}`
- **Distilled by:** `{model}`

## Objective

{objective}

## Trigger

{trigger}

## Success / acceptance criteria

The loop succeeds only when these are observably true (never report an error or an
exhausted budget as success):

{_md_list(skill.acceptance, "Define an observable acceptance check before running.")}

## Feedback cycle

Each pass follows Loopy's Observe → Choose → Act → Verify → Record → Repeat/stop:

1. **Observe** — read fresh page state and the agreed evidence.
2. **Choose** — pick the next checkpoint from the worklist:
{chr(10).join(f"   - {m}" for m in skill.milestones) or "   - (derive checkpoints from the skill procedure)"}
3. **Act** — take one bounded, reversible action toward that checkpoint.
4. **Verify** — re-run the acceptance check; do not confuse these *false terminal
   states* with success:
{chr(10).join(f"   - {f}" for f in skill.false_terminals) or "   - (none recorded)"}
5. **Record** — save the action, evidence, outcome, and remaining work.
6. **Repeat or stop** — continue only while progress is measurable and the boundary
   holds. On failure, apply a recovery policy and learn:
{chr(10).join(f"   - {r}" for r in skill.recovery) or "   - (retry the failed checkpoint once, then escalate)"}

## Stopping conditions

- **Terminal states:** Success · Clean no-op · Blocked · Approval required ·
  Exhausted · No progress.
- **Run boundary:** {boundary}.
- **No-progress stop:** halt when a pass produces no measurable change toward the
  acceptance criteria.

## Governance

- **Approval gate:** side-effecting browser actions (logins, submissions,
  purchases, external messages) require explicit human approval before they run.
  Without approval the loop halts at **Approval required**.
- **Red lines (never violate):**
{_md_list(skill.red_lines, "No irreversible or out-of-scope actions.")}
- **Security boundaries:**
{_md_list(skill.security, "Only act on HTTPS pages whose domain matches the intended target.")}
- **Traceability:** every run emits an audit event and a run receipt
  (see `integration/governance/` and `integration/core/receipt.py`).

Prompt:
> {prompt}

---
_Generated from `{skill.source}` (SHA-256 `{skill.sha256[:16]}…`) by
`integration/core/skill_to_loop.py`. This is a ForgeLoop adaptation of the Forge
skill into a Loopy-style loop — not a published Loop Library loop._
"""


def skill_to_loop(path: str | Path, *, max_passes: int | None = None) -> tuple[Skill, str]:
    skill = parse_skill(path)
    return skill, render_loop_md(skill, max_passes=max_passes)


# ──────────────────────────── CLI ──────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Convert a Forge SKILL.md into a Loopy loop.md")
    ap.add_argument("skill", help="Path to SKILL.md")
    ap.add_argument("--out", help="Write loop.md here (default: stdout)")
    ap.add_argument("--max-passes", type=int, default=None, help="Operator-supplied run boundary")
    ap.add_argument("--no-audit", action="store_true", help="Do not record a governance audit event")
    args = ap.parse_args(argv)

    skill, loop_md = skill_to_loop(args.skill, max_passes=args.max_passes)

    if not args.no_audit:
        try:
            from ..governance.audit import record_event
            record_event(
                actor="system",
                kind="loop.created",
                subject=skill.id,
                detail={"source": skill.source, "sha256": skill.sha256,
                        "out": args.out or "(stdout)"},
            )
        except Exception as e:  # noqa: BLE001  (audit must never block the transform)
            print(f"[warn] audit not recorded: {e}", file=sys.stderr)

    if args.out:
        Path(args.out).write_text(loop_md)
        print(f"wrote {args.out}  (skill {skill.id}, {len(skill.milestones)} milestones, "
              f"{len(skill.acceptance)} acceptance checks, {len(skill.red_lines)} red lines)")
    else:
        sys.stdout.write(loop_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
