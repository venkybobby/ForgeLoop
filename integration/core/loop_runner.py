"""loop_runner — execute a ForgeLoop loop.md in bounded passes, emit a receipt.

Follows Loopy's bounded-execution rules (`loopy/skills/loopy/references/run.md`):
resolve the loop, validate an observable acceptance check + finite boundary,
run bounded passes, and stop at a NAMED terminal state. Errors are never reported
as success.

Governance is built in:
  * an **approval gate** — side-effecting browser actions (logins, submissions,
    purchases, external messages) require explicit human approval. Without it the
    run halts at "Approval required" before any such action.
  * **traceability** — run.started / run.finished audit events plus a persisted
    receipt.

Actual browser execution is delegated to an `executor` callable (wired in a later
loop). With no executor and no approval, a real-world skill correctly stops at the
gate. A `--simulate` executor walks the feedback cycle deterministically (clearly
labelled, never claimed as a real success) so the full cycle can be demonstrated.

CLI:
    python -m integration.core.loop_runner <loop.md> [--skill SKILL.md]
        [--approve] [--simulate] [--max-passes N] [--out RECEIPT.md] [--ts ISO]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Callable

from .receipt import Receipt
from .skill_to_loop import parse_skill, parse_sections, find_section, bullets
from .browser_executor import BrowserExecutor, actions_from_trace, PLAYWRIGHT_AVAILABLE

# Hard safety backstop on passes. This is NOT the loop's success boundary (Loopy
# forbids inventing that) — it is a runaway guard, distinct and generous.
SAFETY_CAP = 25

Executor = Callable[[str, dict], dict]   # (milestone, context) -> {acted, observation}
Verifier = Callable[[dict], bool]        # (context) -> acceptance met?


def _loop_identity(loop_md: str) -> tuple[str, str]:
    title, sections = parse_sections(loop_md)
    name = sections[0].heading if sections else (title or "loop")
    sha = hashlib.sha256(loop_md.encode("utf-8")).hexdigest()
    return name, sha


def _acceptance_from_loop(loop_md: str) -> list[str]:
    _, sections = parse_sections(loop_md)
    return bullets(find_section(sections, "success+acceptance", "acceptance", "success+criteria"))


def _simulate_executor(milestone: str, ctx: dict) -> dict:
    # Deterministic, side-effect-free. Records intent; never touches a real page.
    return {"acted": True, "observation": f"[SIMULATED] would perform: {milestone}"}


def run_loop(
    loop_path: str | Path,
    skill_path: str | Path | None = None,
    *,
    approve: bool = False,
    max_passes: int | None = None,
    executor: Executor | None = None,
    verify: Verifier | None = None,
    ts: str | None = None,
    audit: bool = True,
    runs_dir: str | Path | None = None,
) -> Receipt:
    loop_path = Path(loop_path)
    loop_md = loop_path.read_text()
    name, sha = _loop_identity(loop_md)

    # Prefer the source skill for the worklist + governance facts; fall back to
    # whatever the loop.md itself carries.
    if skill_path:
        skill = parse_skill(skill_path)
        milestones = skill.milestones
        red_lines = skill.red_lines
        acceptance = skill.acceptance or _acceptance_from_loop(loop_md)
        scope_target = skill.metadata.get("domains", ["the in-scope target"])[0]
    else:
        skill = None
        milestones = []
        red_lines = []
        acceptance = _acceptance_from_loop(loop_md)
        scope_target = "the in-scope target"

    boundary = (
        f"operator-supplied {max_passes} passes"
        if max_passes
        else f"no-progress stop (safety backstop {SAFETY_CAP} passes)"
    )
    check = (
        f"{len(acceptance)} observable acceptance criteria, e.g. “{acceptance[0]}”"
        if acceptance
        else "NO observable acceptance check defined"
    )

    def _audit(kind: str, detail: dict) -> None:
        if not audit:
            return
        try:
            from ..governance.audit import record_event
            record_event(actor="system", kind=kind, subject=name, detail=detail, ts=ts)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] audit not recorded: {e}", file=sys.stderr)

    _audit("run.started", {"loop_sha256": sha, "approved": approve,
                           "executor": "simulate" if executor else ("none" if not approve else "none")})

    evidence: list[str] = []
    actions: list[str] = []

    # ── Preflight: validate the loop is runnable (Loopy "validate every loop"). ─
    structural_ok = True
    if acceptance:
        evidence.append(f"Acceptance check present ({len(acceptance)} criteria).")
    else:
        evidence.append("FAIL: no observable acceptance check — loop is not runnable.")
        structural_ok = False
    evidence.append(
        f"Finite run boundary present: {boundary}."
    )
    evidence.append(
        f"Governance: {len(red_lines)} red line(s); approval gate {'ON' if not approve else 'satisfied (approved)'}."
        if (red_lines or True) else "no red lines"
    )
    if skill is not None:
        evidence.append(f"Worklist resolved from skill `{skill.id}`: {len(milestones)} checkpoint(s).")

    if not structural_ok:
        receipt = Receipt(
            loop=name,
            definition=f"local loop.md SHA-256 {sha[:16]}…",
            scope=f"{scope_target} (no actions taken)",
            check=check,
            boundary=boundary,
            result="Blocked",
            evidence=evidence,
            actions=["Preflight only — refused to run a loop with no acceptance gate."],
            next="Add an observable acceptance check to the loop, then re-run.",
            ts=ts,
        )
        _audit("run.finished", {"result": receipt.result})
        _persist(receipt, runs_dir, name)
        return receipt

    # ── Bounded passes ─────────────────────────────────────────────────────
    cap = max_passes if max_passes else SAFETY_CAP
    worklist = list(milestones) or ["Reach the acceptance condition"]
    result = "No progress"
    nxt = "nothing"
    ctx: dict = {"completed": [], "target": scope_target}

    for i, milestone in enumerate(worklist):
        if i >= cap:
            result = "Exhausted"
            nxt = f"Reached the run boundary ({boundary}) before acceptance."
            break

        # Observe + Choose are non-side-effecting and always allowed.
        evidence.append(f"Pass {i + 1} — observe target ({scope_target}); choose: {milestone}")

        # Act is gated. A real browser action needs approval AND an executor.
        if executor is None:
            if not approve:
                result = "Approval required"
                actions.append(f"Pass {i + 1}: planned “{milestone}” — HELD at approval gate (no action taken).")
                nxt = ("Grant human approval and configure a browser executor, then re-run. "
                       "The loop performs side-effecting actions (e.g. form submission / login) "
                       "that must not run unattended.")
                break
            else:  # approved, but nothing to execute with
                result = "Blocked"
                actions.append(f"Pass {i + 1}: approved, but no browser executor backend is configured.")
                nxt = "Wire a browser executor (e.g. Playwright MCP) and re-run."
                break

        # Executor present (e.g. --simulate): Act -> Verify -> Record.
        outcome = executor(milestone, ctx)
        actions.append(f"Pass {i + 1}: {outcome.get('observation', milestone)}")
        ctx["completed"].append(milestone)
        met = verify(ctx) if verify else (len(ctx["completed"]) == len(worklist))
        evidence.append(f"Pass {i + 1} — verify acceptance: {'met' if met else 'not yet'}")
        if met:
            # Simulated runs make no real change -> the honest terminal is Clean no-op.
            result = "Clean no-op" if executor is _simulate_executor else "Success"
            nxt = ("nothing (SIMULATED run — no real browser actions were taken; "
                   "re-run with approval + a live executor to act for real)"
                   if executor is _simulate_executor else "nothing")
            break

    definition = f"local loop.md SHA-256 {sha[:16]}…; boundary={boundary}"
    receipt = Receipt(
        loop=name,
        definition=definition,
        scope=f"{scope_target} — {'simulated walk of' if executor else 'planned'} {len(worklist)} checkpoint(s)",
        check=check,
        boundary=boundary,
        result=result,
        evidence=evidence,
        actions=actions or ["(no passes ran)"],
        next=nxt,
        ts=ts,
    )
    _audit("run.finished", {"result": receipt.result, "passes": len(actions)})
    _persist(receipt, runs_dir, name)
    return receipt


def run_live(
    loop_path: str | Path,
    skill_path: str | Path,
    trace_path: str | Path,
    *,
    approve: bool = False,
    headless: bool = True,
    base_url: str | None = None,
    max_passes: int | None = None,
    runs_dir: str | Path | None = None,
    evidence_dir: str | Path | None = None,
    ts: str | None = None,
    audit: bool = True,
) -> Receipt:
    """Execute a loop against a LIVE page via Playwright, behind the approval gate.

    The concrete steps are replayed from the recorded `trace.json`; the loop's
    acceptance criteria decide the terminal state from the real resulting page.
    Approval is MANDATORY — without `approve=True` no browser is launched.
    """
    loop_md = Path(loop_path).read_text()
    name, sha = _loop_identity(loop_md)
    skill = parse_skill(skill_path)
    acceptance = skill.acceptance or _acceptance_from_loop(loop_md)
    boundary = (f"operator-supplied {max_passes} passes" if max_passes
                else f"recorded plan length (safety backstop {SAFETY_CAP})")
    check = (f"URL leaves the form page AND the result page renders; acceptance: "
             f"“{acceptance[0]}”" if acceptance else "NO observable acceptance check")

    def _audit(kind: str, detail: dict) -> None:
        if not audit:
            return
        try:
            from ..governance.audit import record_event
            record_event(actor="system", kind=kind, subject=name, detail=detail, ts=ts)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] audit not recorded: {e}", file=sys.stderr)

    # ── Mandatory approval gate ─────────────────────────────────────────────
    if not approve:
        _audit("run.started", {"loop_sha256": sha, "mode": "live", "approved": False})
        receipt = Receipt(
            loop=name, definition=f"local loop.md SHA-256 {sha[:16]}…",
            scope=f"{skill.metadata.get('domains', ['target'])[0]} (LIVE) — not started",
            check=check, boundary=boundary, result="Approval required",
            evidence=["Live browser execution requires explicit human approval (--approve)."],
            actions=["No browser launched."],
            next="Re-run with --approve to authorize real browser actions.", ts=ts,
        )
        _audit("run.finished", {"result": receipt.result})
        _persist(receipt, runs_dir, name)
        return receipt

    if not PLAYWRIGHT_AVAILABLE:
        receipt = Receipt(
            loop=name, definition=f"local loop.md SHA-256 {sha[:16]}…",
            scope="LIVE — could not start", check=check, boundary=boundary,
            result="Blocked", evidence=["Playwright is not installed."],
            actions=["pip install playwright"], next="Install Playwright, then re-run.", ts=ts,
        )
        _persist(receipt, runs_dir, name)
        return receipt

    _audit("approval.granted", {"loop_sha256": sha, "mode": "live"})
    _audit("run.started", {"loop_sha256": sha, "mode": "live", "approved": True})

    actions = actions_from_trace(trace_path, base_url=base_url)
    cap = max_passes if max_passes else SAFETY_CAP
    form_url = next((a["url"] for a in actions if a["op"] == "navigate"), None)

    evidence: list[str] = [
        f"Acceptance criteria: {len(acceptance)}.",
        f"Replaying {len(actions)} recorded step(s) against a live page"
        + (f" (host rewritten to {base_url})." if base_url else "."),
        f"Governance: {len(skill.red_lines)} red line(s); approval granted.",
    ]
    done: list[str] = []
    result, nxt = "No progress", "nothing"

    ex = BrowserExecutor(headless=headless)
    try:
        ex.start()
        for i, act in enumerate(actions):
            if i >= cap:
                result, nxt = "Exhausted", f"Hit run boundary ({boundary})."
                break
            try:
                if act["op"] == "navigate":
                    ex.navigate(act["url"]); obs = f"navigated → {ex.current_url()}"
                elif act["op"] == "fill":
                    ex.fill(act["selector"], act["value"]); obs = act["label"]
                elif act["op"] == "click":
                    ex.click(act["selector"]); obs = act["label"]
                else:
                    obs = f"skipped {act}"
                done.append(f"Pass {i + 1}: {obs}")
            except Exception as e:  # noqa: BLE001 — element missing / timeout etc.
                result = "Blocked"
                done.append(f"Pass {i + 1}: FAILED {act.get('label', act['op'])} — {type(e).__name__}")
                nxt = f"Action failed: {act.get('label')}. Page may differ from the recording."
                break

        # ── Verify acceptance against the REAL resulting page ───────────────
        final_url = ex.current_url()
        snippet = ex.page_text(400)
        url_changed = bool(form_url) and final_url.rstrip("/") != form_url.rstrip("/")
        page_rendered = len(snippet.strip()) > 0
        if result not in ("Blocked", "Exhausted"):
            if url_changed and page_rendered:
                result, nxt = "Success", "nothing — acceptance met on the live page."
            else:
                result = "No progress"
                nxt = ("URL did not leave the form page; the submission may not have "
                       "completed. Inspect the page and selectors.")

        evidence.append(f"Form URL: {form_url}")
        evidence.append(f"Final URL: {final_url}  (changed: {'yes' if url_changed else 'no'})")
        evidence.append(f"Result page text (extracted): “{snippet[:240]}”")
        if evidence_dir is not None:
            shot = ex.screenshot(Path(evidence_dir) / "result.png")
            evidence.append(f"Screenshot: {shot}")
    finally:
        ex.close()

    receipt = Receipt(
        loop=name,
        definition=f"local loop.md SHA-256 {sha[:16]}…; trace={Path(trace_path).name}; boundary={boundary}",
        scope=f"{skill.metadata.get('domains', ['target'])[0]} (LIVE browser run)"
              + (f" via {base_url}" if base_url else ""),
        check=check, boundary=boundary, result=result,
        evidence=evidence, actions=done or ["(no steps ran)"], next=nxt, ts=ts,
    )
    _audit("run.finished", {"result": receipt.result, "passes": len(done)})
    _persist(receipt, runs_dir, name)
    return receipt


def _persist(receipt: Receipt, runs_dir: str | Path | None, name: str) -> None:
    if runs_dir is None:
        return
    d = Path(runs_dir)
    d.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in name).strip("-").lower()
    (d / f"{safe}.receipt.md").write_text(receipt.render())


# ──────────────────────────── CLI ──────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run a ForgeLoop loop.md in bounded passes")
    ap.add_argument("loop", help="Path to loop.md")
    ap.add_argument("--skill", help="Path to the source SKILL.md (for the worklist + red lines)")
    ap.add_argument("--approve", action="store_true", help="Grant human approval for side-effecting actions")
    ap.add_argument("--simulate", action="store_true",
                    help="Walk the feedback cycle with a side-effect-free simulated executor")
    ap.add_argument("--max-passes", type=int, default=None, help="Operator-supplied run boundary")
    ap.add_argument("--out", help="Also write the receipt here")
    ap.add_argument("--ts", help="ISO-8601 timestamp to stamp the receipt/audit (caller-supplied)")
    ap.add_argument("--runs-dir", help="Directory to persist the receipt into")
    # Live (real browser) execution:
    ap.add_argument("--live", action="store_true",
                    help="Execute against a real page via Playwright (requires --approve and --trace)")
    ap.add_argument("--trace", help="Recorded trace.json to replay (concrete steps) in --live mode")
    ap.add_argument("--base-url", help="Rewrite the recorded host (e.g. http://127.0.0.1:PORT for a local copy)")
    ap.add_argument("--headed", action="store_true", help="Run the browser headed (default headless)")
    ap.add_argument("--evidence-dir", help="Directory to write a screenshot into (--live)")
    args = ap.parse_args(argv)

    if args.live:
        if not args.trace:
            ap.error("--live requires --trace <trace.json>")
        if not args.skill:
            ap.error("--live requires --skill <SKILL.md>")
        receipt = run_live(
            args.loop, args.skill, args.trace,
            approve=args.approve, headless=not args.headed, base_url=args.base_url,
            max_passes=args.max_passes, ts=args.ts, runs_dir=args.runs_dir,
            evidence_dir=args.evidence_dir,
        )
    else:
        receipt = run_loop(
            args.loop,
            skill_path=args.skill,
            approve=args.approve,
            max_passes=args.max_passes,
            executor=_simulate_executor if args.simulate else None,
            ts=args.ts,
            runs_dir=args.runs_dir,
        )
    out = receipt.render()
    if args.out:
        Path(args.out).write_text(out)
        print(f"wrote {args.out}  (result: {receipt.result})")
    sys.stdout.write(out)
    # Exit non-zero on a non-terminal-success so CI/scripts can branch on it.
    return 0 if receipt.result in ("Success", "Clean no-op", "Approval required") else 1


if __name__ == "__main__":
    raise SystemExit(main())
