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
        + (["--out", args.out] if args.out else [])
        + (["--runs-dir", args.runs_dir] if args.runs_dir else [])
        + (["--max-passes", str(args.max_passes)] if args.max_passes else [])
    )


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
    r.add_argument("--approve", action="store_true")
    r.add_argument("--simulate", action="store_true")
    r.add_argument("--out")
    r.add_argument("--runs-dir")
    r.add_argument("--max-passes", type=int)
    r.set_defaults(fn=_cmd_run)

    a = sub.add_parser("audit", help="print the governance trail")
    a.add_argument("--subject")
    a.add_argument("-v", "--verbose", action="store_true")
    a.set_defaults(fn=_cmd_audit)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
