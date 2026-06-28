"""forgeloop — one CLI over the integration layer.

    python -m integration.cli.forgeloop bind  <SKILL.md> [--out loop.md] [--max-passes N]
    python -m integration.cli.forgeloop run   <loop.md> [--skill SKILL.md] [--approve]
                                              [--simulate] [--out RECEIPT.md] [--runs-dir DIR]
    python -m integration.cli.forgeloop audit [--subject ID]

`bind` turns a Forge skill into a Loopy loop; `run` executes it in bounded passes
and prints a receipt; `audit` prints the governance trail.
"""

from __future__ import annotations

import argparse
import json
import sys

from ..core import skill_to_loop as s2l
from ..core import loop_runner
from ..governance import audit


def _cmd_bind(args: argparse.Namespace) -> int:
    return s2l.main(
        [args.skill]
        + (["--out", args.out] if args.out else [])
        + (["--max-passes", str(args.max_passes)] if args.max_passes else [])
    )


def _cmd_run(args: argparse.Namespace) -> int:
    return loop_runner.main(
        [args.loop]
        + (["--skill", args.skill] if args.skill else [])
        + (["--approve"] if args.approve else [])
        + (["--simulate"] if args.simulate else [])
        + (["--live"] if args.live else [])
        + (["--trace", args.trace] if args.trace else [])
        + (["--base-url", args.base_url] if args.base_url else [])
        + (["--headed"] if args.headed else [])
        + (["--evidence-dir", args.evidence_dir] if args.evidence_dir else [])
        + (["--out", args.out] if args.out else [])
        + (["--runs-dir", args.runs_dir] if args.runs_dir else [])
        + (["--max-passes", str(args.max_passes)] if args.max_passes else [])
    )


def _cmd_status(args: argparse.Namespace) -> int:
    events = audit.read_events()
    if not events:
        print("No runs yet. Bind a skill (`forgeloop bind`) then run it (`forgeloop run`).")
        return 0
    by_kind: dict[str, int] = {}
    for ev in events:
        by_kind[ev["kind"]] = by_kind.get(ev["kind"], 0) + 1
    print("ForgeLoop status")
    print(f"  audit events: {len(events)}")
    for k in sorted(by_kind):
        print(f"    {k:<18} {by_kind[k]}")
    finished = [e for e in events if e["kind"] == "run.finished"]
    if finished:
        print("  recent run results:")
        for e in finished[-5:]:
            res = e.get("detail", {}).get("result", "?")
            print(f"    {e['ts']}  {e['subject']:<40} {res}")
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    events = audit.read_events(subject=args.subject)
    if not events:
        print("(no audit events)")
        return 0
    for ev in events:
        print(f"{ev['ts']}  {ev['actor']:<7} {ev['kind']:<18} {ev['subject']}")
        if args.verbose and ev.get("detail"):
            print(f"    {json.dumps(ev['detail'], ensure_ascii=False)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="forgeloop", description="ForgeLoop integration CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bind", help="SKILL.md -> loop.md")
    b.add_argument("skill")
    b.add_argument("--out")
    b.add_argument("--max-passes", type=int)
    b.set_defaults(fn=_cmd_bind)

    r = sub.add_parser("run", help="run a loop.md, emit a receipt")
    r.add_argument("loop")
    r.add_argument("--skill")
    r.add_argument("--approve", action="store_true", help="grant human approval for side-effecting actions")
    r.add_argument("--simulate", action="store_true", help="side-effect-free walk of the feedback cycle")
    r.add_argument("--live", action="store_true", help="real browser via Playwright (needs --approve + --trace)")
    r.add_argument("--trace", help="recorded trace.json to replay in --live mode")
    r.add_argument("--base-url", help="rewrite the recorded host, e.g. http://127.0.0.1:PORT")
    r.add_argument("--headed", action="store_true")
    r.add_argument("--evidence-dir")
    r.add_argument("--out")
    r.add_argument("--runs-dir")
    r.add_argument("--max-passes", type=int)
    r.set_defaults(fn=_cmd_run)

    a = sub.add_parser("audit", help="print the governance trail")
    a.add_argument("--subject")
    a.add_argument("-v", "--verbose", action="store_true")
    a.set_defaults(fn=_cmd_audit)

    s = sub.add_parser("status", help="summarize runs from the audit trail")
    s.set_defaults(fn=_cmd_status)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
