#!/usr/bin/env python3
"""agentic_demo — run an example with the LLM-driven (agentic) executor.

    python scripts/agentic_demo.py [form-fill|login-flow]

If SF_LLM_KEY is set, the next action at each step is chosen by the LLM against
the live DOM (fully autonomous). Otherwise a deterministic chooser derived from
the recording stands in — still exercising the full observe→choose→act→verify
loop, just with scripted choices — so the agentic path is reproducible offline.

Targets the example's local page copy (the sandbox blocks public egress).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from integration.core.llm_executor import run_agentic, make_llm_chooser, values_from_trace  # noqa: E402
from integration.core.browser_executor import actions_from_trace  # noqa: E402


def _scripted_chooser(trace_path: Path):
    acts = [a for a in actions_from_trace(trace_path) if a["op"] in ("fill", "click")]
    steps = [{"action": a["op"], "selector": a["selector"], "value": a.get("value", "")} for a in acts]
    steps.append({"action": "stop", "done": True, "thought": "recorded plan complete"})

    def chooser(step: int, ctx: dict) -> dict:
        return steps[step] if step < len(steps) else {"action": "stop", "done": True}
    return chooser


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "form-fill"
    ex = ROOT / "examples" / name
    spec = importlib.util.spec_from_file_location(f"{name}_srv", ex / "local_server.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    httpd, base_url = mod.serve(0)

    first_nav = next((a["url"] for a in actions_from_trace(ex / "trace.json", base_url=base_url)
                      if a["op"] == "navigate"), base_url)

    if os.environ.get("SF_LLM_KEY"):
        chooser = make_llm_chooser(values_from_trace(ex / "trace.json"))
        print(f"[agentic] using LLM chooser ({os.environ.get('SF_DISTILL_MODEL', 'default model')})")
    else:
        chooser = _scripted_chooser(ex / "trace.json")
        print("[agentic] SF_LLM_KEY not set — using a scripted chooser (offline reproducible)")

    try:
        receipt = run_agentic(
            ex / "loop.md", ex / "SKILL.md", chooser=chooser, start_url=first_nav,
            approve=True, headless=True, evidence_dir=ex / "evidence",
            ts=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        httpd.shutdown()

    (ex / "RECEIPT.agentic.md").write_text(receipt.render())
    print(f"[agentic] result: {receipt.result}  -> wrote {ex / 'RECEIPT.agentic.md'}")
    return 0 if receipt.result == "Success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
