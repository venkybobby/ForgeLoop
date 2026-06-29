"""build — generate a self-contained static dashboard for ForgeLoop.

Reads the loop catalog (`integration/core/catalog.py`) and the governance audit
trail, and bakes them into a single `index.html` with no runtime dependency — it
opens straight from disk (`file://`), no server needed.

    python -m integration.dashboard.build [--root examples] [--out PATH]
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from ..core.catalog import build_catalog, CatalogEntry

_RESULT_COLOR = {
    "Success": "#137333", "Clean no-op": "#1a73e8", "Approval required": "#b06000",
    "Blocked": "#b3261e", "No progress": "#7a4f01", "Exhausted": "#7a4f01",
}


def _badge(result: str | None) -> str:
    if not result:
        return '<span class="muted">—</span>'
    color = _RESULT_COLOR.get(result, "#444")
    return f'<span class="badge" style="background:{color}">{html.escape(result)}</span>'


def _catalog_rows(entries: list[CatalogEntry]) -> str:
    if not entries:
        return '<tr><td colspan="6" class="muted">No skills found.</td></tr>'
    out = []
    for e in entries:
        loop = "✅" if e.has_loop else "—"
        rcpt = "✅" if e.has_receipt else "—"
        out.append(
            f"<tr><td><code>{html.escape(e.id)}</code><br><span class='muted'>"
            f"{e.milestones} milestones · {e.red_lines} red lines</span></td>"
            f"<td>{html.escape(e.domain)}</td><td>{html.escape(e.model)}</td>"
            f"<td class='c'>{loop}</td><td class='c'>{rcpt}</td>"
            f"<td>{_badge(e.last_result)}</td></tr>"
        )
    return "\n".join(out)


def _run_rows(events: list[dict]) -> str:
    finished = [e for e in events if e.get("kind") == "run.finished"][-15:][::-1]
    if not finished:
        return '<tr><td colspan="3" class="muted">No runs yet.</td></tr>'
    out = []
    for e in finished:
        res = e.get("detail", {}).get("result")
        out.append(
            f"<tr><td class='muted'>{html.escape(e.get('ts', ''))}</td>"
            f"<td>{html.escape(e.get('subject', ''))}</td><td>{_badge(res)}</td></tr>"
        )
    return "\n".join(out)


def build_html(root: str | Path = "examples", *, generated_at: str = "") -> str:
    entries = build_catalog(root)
    try:
        from ..governance.audit import read_events
        events = read_events()
    except Exception:  # noqa: BLE001
        events = []
    n_success = sum(1 for e in entries if e.last_result == "Success")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ForgeLoop dashboard</title>
<style>
  body{{font:14px/1.5 system-ui,sans-serif;margin:0;background:#f6f8fa;color:#1f2328}}
  header{{background:#0d1117;color:#fff;padding:18px 24px}}
  header h1{{margin:0;font-size:18px}} header p{{margin:4px 0 0;color:#9da7b1}}
  main{{max-width:980px;margin:24px auto;padding:0 16px}}
  .cards{{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}}
  .card{{background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:14px 18px;min-width:120px}}
  .card b{{font-size:22px;display:block}}
  h2{{font-size:15px;margin:22px 0 8px}}
  table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d0d7de;border-radius:8px;overflow:hidden}}
  th,td{{text-align:left;padding:8px 12px;border-bottom:1px solid #eaeef2;vertical-align:top}}
  th{{background:#f6f8fa;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#57606a}}
  td.c{{text-align:center}} code{{background:#eff1f3;padding:1px 5px;border-radius:4px;font-size:12px}}
  .muted{{color:#8b949e;font-size:12px}}
  .badge{{color:#fff;padding:2px 8px;border-radius:999px;font-size:12px;white-space:nowrap}}
  footer{{max-width:980px;margin:16px auto 40px;padding:0 16px;color:#8b949e;font-size:12px}}
</style></head>
<body>
<header><h1>ForgeLoop dashboard</h1><p>Forge skills → governed Loopy loops → runs</p></header>
<main>
  <div class="cards">
    <div class="card"><b>{len(entries)}</b>skills / loops</div>
    <div class="card"><b>{n_success}</b>with a Success run</div>
    <div class="card"><b>{len(events)}</b>audit events</div>
  </div>

  <h2>Catalog</h2>
  <table><thead><tr><th>Skill / loop</th><th>Domain</th><th>Model</th><th>loop.md</th>
    <th>receipt</th><th>last run</th></tr></thead>
    <tbody>{_catalog_rows(entries)}</tbody></table>

  <h2>Recent runs</h2>
  <table><thead><tr><th>When</th><th>Loop</th><th>Result</th></tr></thead>
    <tbody>{_run_rows(events)}</tbody></table>
</main>
<footer>Static snapshot{(' · generated ' + html.escape(generated_at)) if generated_at else ''} ·
  read-only view of the catalog + governance audit trail. Regenerate with
  <code>python -m integration.dashboard.build</code>.</footer>
</body></html>"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the ForgeLoop static dashboard")
    ap.add_argument("--root", default="examples", help="Where to scan for skills")
    ap.add_argument("--out", default="integration/dashboard/index.html")
    ap.add_argument("--generated-at", default="", help="Optional timestamp to stamp (caller-supplied)")
    args = ap.parse_args(argv)
    htmltext = build_html(args.root, generated_at=args.generated_at)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(htmltext)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
