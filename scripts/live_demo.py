#!/usr/bin/env python3
"""live_demo — a real, reproducible Inner-Loop-3 run for the form-fill example.

Starts the local copy of the order form (public egress is blocked in the
sandbox), then runs the form-fill loop LIVE through Playwright behind the approval
gate, replaying the recorded trace against the real page and verifying acceptance
from the actual result page. Writes a real receipt + screenshot.

    python scripts/live_demo.py
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load the example's local form server (its dir name has a dash → load by path).
_spec = importlib.util.spec_from_file_location(
    "local_server", ROOT / "examples" / "form-fill" / "local_server.py"
)
local_server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(local_server)  # type: ignore[union-attr]

from integration.core.loop_runner import run_live  # noqa: E402

EX = ROOT / "examples" / "form-fill"


def main() -> int:
    httpd, base_url = local_server.serve(0)
    print(f"[demo] local form server at {base_url}/forms/post")
    try:
        receipt = run_live(
            EX / "loop.md",
            EX / "SKILL.md",
            EX / "trace.json",
            approve=True,                       # mandatory for a live run
            headless=True,
            base_url=base_url,                  # replay the recording against the local copy
            evidence_dir=EX / "evidence",
            runs_dir=None,
            ts=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        httpd.shutdown()

    (EX / "RECEIPT.live.md").write_text(receipt.render())
    print(f"[demo] result: {receipt.result}")
    print(f"[demo] wrote {EX / 'RECEIPT.live.md'}")
    sys.stdout.write("\n" + receipt.render())
    return 0 if receipt.result == "Success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
