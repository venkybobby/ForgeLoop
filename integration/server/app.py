"""app — the ForgeLoop web control plane (stdlib HTTP, zero-dependency).

A browser UI + JSON API over the integration layer, so the whole product is
usable from any browser and deployable anywhere (see the Dockerfile):

  GET  /                        dashboard UI (catalog, runs, approve button)
  GET  /api/catalog             skills/loops + latest result
  GET  /api/runs                run records (newest first)
  GET  /api/runs/<id>           one run + its receipt
  POST /api/loops/<id>/run      start a run  {mode: simulate|live}
  POST /api/runs/<id>/approve   approve a pending live run -> executes -> receipt

Live runs honour the approval gate: `mode=live` creates a **pending** run; nothing
touches a browser until `/approve`. For the bundled examples, an approved live run
spins up the example's local page copy (the sandbox blocks public egress); in a
real deployment the loop targets the recorded site directly.
"""

from __future__ import annotations

import importlib.util
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ..core import catalog as catalog_mod
from ..core import loop_runner
from ..core.loop_runner import run_loop, run_live, _simulate_executor
from ..governance import runs as runstore

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entry_dir(loop_id: str) -> Path | None:
    for e in catalog_mod.build_catalog(EXAMPLES):
        if e.id == loop_id:
            return Path(e.skill_path).parent
    return None


def _maybe_local_server(example_dir: Path):
    """Start the example's local page copy if present; return (httpd|None, base_url|None)."""
    srv = example_dir / "local_server.py"
    if not srv.exists():
        return None, None
    spec = importlib.util.spec_from_file_location(f"{example_dir.name}_srv", srv)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.serve(0)


# ──────────────────────────── actions ──────────────────────────────────────
def start_run(loop_id: str, mode: str) -> dict:
    d = _entry_dir(loop_id)
    if d is None:
        return {"error": f"unknown loop {loop_id}"}
    loop_md, skill_md, trace = d / "loop.md", d / "SKILL.md", d / "trace.json"
    if mode == "simulate":
        rec = runstore.create(loop_id=loop_id, loop_path=str(loop_md), skill_path=str(skill_md),
                              trace_path=str(trace), mode="simulate", status=runstore.RUNNING)
        receipt = run_loop(loop_md, skill_path=skill_md, executor=_simulate_executor, ts=_now())
        runstore.finish(rec, receipt)
        return {"run_id": rec.run_id, "status": rec.status, "result": rec.result}
    if mode == "live":
        # Pending: nothing runs until approval.
        rec = runstore.create(loop_id=loop_id, loop_path=str(loop_md), skill_path=str(skill_md),
                              trace_path=str(trace), mode="live", status=runstore.PENDING)
        return {"run_id": rec.run_id, "status": rec.status,
                "result": "Approval required", "needs_approval": True}
    return {"error": f"unknown mode {mode}"}


def approve_run(run_id: str) -> dict:
    rec = runstore.get(run_id)
    if rec is None:
        return {"error": f"unknown run {run_id}"}
    if rec.status != runstore.PENDING:
        return {"error": f"run {run_id} is not pending (status {rec.status})"}
    rec.approved_ts = _now()
    rec.status = runstore.RUNNING
    rec.save()
    d = Path(rec.skill_path).parent
    httpd, base_url = _maybe_local_server(d)
    try:
        receipt = run_live(rec.loop_path, rec.skill_path, rec.trace_path,
                           approve=True, headless=True, base_url=base_url,
                           evidence_dir=d / "evidence", ts=_now())
    finally:
        if httpd:
            httpd.shutdown()
    rec.base_url = base_url
    runstore.finish(rec, receipt)
    return {"run_id": rec.run_id, "status": rec.status, "result": rec.result}


# ──────────────────────────── HTTP handler ─────────────────────────────────
class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text, code=200):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            return self._html(PAGE)
        if p == "/api/catalog":
            return self._json(catalog_mod.to_dicts(catalog_mod.build_catalog(EXAMPLES)))
        if p == "/api/runs":
            return self._json([_run_brief(r) for r in runstore.list_runs()])
        if p.startswith("/api/runs/"):
            rec = runstore.get(p.rsplit("/", 1)[-1])
            return self._json(rec.__dict__ if rec else {"error": "not found"},
                              200 if rec else 404)
        return self._json({"error": "not found"}, 404)

    def do_POST(self):  # noqa: N802
        p = self.path.split("?")[0]
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        if p.startswith("/api/loops/") and p.endswith("/run"):
            loop_id = p[len("/api/loops/"):-len("/run")]
            return self._json(start_run(loop_id, body.get("mode", "simulate")))
        if p.startswith("/api/runs/") and p.endswith("/approve"):
            run_id = p[len("/api/runs/"):-len("/approve")]
            return self._json(approve_run(run_id))
        return self._json({"error": "not found"}, 404)


def _run_brief(r: runstore.RunRecord) -> dict:
    return {"run_id": r.run_id, "loop_id": r.loop_id, "mode": r.mode,
            "status": r.status, "result": r.result, "created_ts": r.created_ts}


def serve(host: str = "127.0.0.1", port: int = 8055) -> None:
    httpd = ThreadingHTTPServer((host, port), _Handler)
    print(f"ForgeLoop web app → http://{host}:{port}/  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1"><title>ForgeLoop</title>
<style>
 body{font:14px/1.5 system-ui,sans-serif;margin:0;background:#f6f8fa;color:#1f2328}
 header{background:#0d1117;color:#fff;padding:16px 24px}header h1{margin:0;font-size:18px}
 header p{margin:4px 0 0;color:#9da7b1}main{max-width:1000px;margin:22px auto;padding:0 16px}
 h2{font-size:15px;margin:22px 0 8px}table{width:100%;border-collapse:collapse;background:#fff;
 border:1px solid #d0d7de;border-radius:8px;overflow:hidden}th,td{text-align:left;padding:8px 12px;
 border-bottom:1px solid #eaeef2;vertical-align:top}th{background:#f6f8fa;font-size:12px;
 text-transform:uppercase;letter-spacing:.04em;color:#57606a}code{background:#eff1f3;padding:1px 5px;
 border-radius:4px;font-size:12px}button{font:inherit;border:1px solid #d0d7de;background:#fff;
 border-radius:6px;padding:4px 10px;cursor:pointer;margin-right:4px}button.primary{background:#1f6feb;
 color:#fff;border-color:#1f6feb}button:disabled{opacity:.5;cursor:default}.badge{color:#fff;
 padding:2px 8px;border-radius:999px;font-size:12px;white-space:nowrap}.muted{color:#8b949e;font-size:12px}
 pre{background:#0d1117;color:#e6edf3;padding:14px;border-radius:8px;overflow:auto;font-size:12px;white-space:pre-wrap}
</style></head><body>
<header><h1>ForgeLoop</h1><p>Forge skills → governed Loopy loops → runs, in your browser</p></header>
<main>
 <h2>Catalog</h2><table id=cat><thead><tr><th>Loop</th><th>Domain</th><th>Model</th>
  <th>Last result</th><th>Run</th></tr></thead><tbody></tbody></table>
 <h2>Runs</h2><table id=runs><thead><tr><th>When</th><th>Loop</th><th>Mode</th>
  <th>Status / result</th><th></th></tr></thead><tbody></tbody></table>
 <h2 id=rh style=display:none>Receipt</h2><pre id=receipt style=display:none></pre>
</main>
<script>
const RC={Success:'#137333','Clean no-op':'#1a73e8','Approval required':'#b06000',
 Blocked:'#b3261e','No progress':'#7a4f01',Exhausted:'#7a4f01',
 'pending-approval':'#b06000',running:'#1a73e8',done:'#137333'};
const badge=t=>t?`<span class=badge style="background:${RC[t]||'#444'}">${t}</span>`:'<span class=muted>—</span>';
async function j(u,o){const r=await fetch(u,o);return r.json()}
async function loadCat(){const c=await j('/api/catalog');
 document.querySelector('#cat tbody').innerHTML=c.map(e=>`<tr>
  <td><code>${e.id}</code><br><span class=muted>${e.milestones} milestones · ${e.red_lines} red lines</span></td>
  <td>${e.domain||''}</td><td>${e.model}</td><td>${badge(e.last_result)}</td>
  <td><button onclick="run('${e.id}','simulate')">Simulate</button>
      <button class=primary onclick="run('${e.id}','live')">Run live</button></td></tr>`).join('')}
async function loadRuns(){const rs=await j('/api/runs');
 document.querySelector('#runs tbody').innerHTML=rs.map(r=>`<tr>
  <td class=muted>${r.created_ts.replace('T',' ').slice(0,19)}</td><td>${r.loop_id}</td><td>${r.mode}</td>
  <td>${badge(r.result||r.status)}</td>
  <td>${r.status==='pending-approval'?`<button class=primary onclick="approve('${r.run_id}')">Approve &amp; run</button>`:''}
      <button onclick="showReceipt('${r.run_id}')">Receipt</button></td></tr>`).join('')}
async function run(id,mode){await j(`/api/loops/${id}/run`,{method:'POST',headers:{'content-type':'application/json'},
  body:JSON.stringify({mode})});await refresh()}
async function approve(rid){const b=event.target;b.disabled=true;b.textContent='Running…';
  await j(`/api/runs/${rid}/approve`,{method:'POST'});await refresh();showReceipt(rid)}
async function showReceipt(rid){const r=await j(`/api/runs/${rid}`);
  document.getElementById('rh').style.display='block';const p=document.getElementById('receipt');
  p.style.display='block';p.textContent=r.receipt_md||'(no receipt yet)';p.scrollIntoView({behavior:'smooth'})}
async function refresh(){await loadCat();await loadRuns()}
refresh();
</script></body></html>"""
