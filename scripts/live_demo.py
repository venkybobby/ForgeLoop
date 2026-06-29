#!/usr/bin/env python3
"""live_demo — a real, reproducible Inner-Loop-3 run for an example.

    python scripts/live_demo.py [form-fill|login-flow]   # default: form-fill

Starts the example's local page copy (public egress is blocked in the sandbox),
then runs its loop LIVE through Playwright behind the approval gate, replaying the
recorded trace against the real page and verifying acceptance from the actual
result page. Writes a real receipt + screenshot into the example folder.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from integration.core.loop_runner import run_live  # noqa: E402


def _load_server(example_dir: Path):
    spec = importlib.util.spec_from_file_location(
        f"{example_dir.name}_local_server", example_dir / "local_server.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "form-fill"
    ex = ROOT / "examples" / name
    if not (ex / "local_server.py").exists():
        print(f"[demo] no local_server.py for example '{name}'", file=sys.stderr)
        return 2

    httpd, base_url = _load_server(ex).serve(0)
    print(f"[demo] {name}: local server at {base_url}")
    try:
        receipt = run_live(
            ex / "loop.md", ex / "SKILL.md", ex / "trace.json",
            approve=True, headless=True, base_url=base_url,
            evidence_dir=ex / "evidence", runs_dir=None,
            ts=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        httpd.shutdown()

    (ex / "RECEIPT.live.md").write_text(receipt.render())
    print(f"[demo] result: {receipt.result}")
    print(f"[demo] wrote {ex / 'RECEIPT.live.md'}")
    sys.stdout.write("\n" + receipt.render())
    return 0 if receipt.result == "Success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
