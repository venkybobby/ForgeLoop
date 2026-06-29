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
import os
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..core import catalog as catalog_mod
from ..core import loop_runner
from ..core.loop_runner import run_loop, run_live, _simulate_executor
from ..governance import runs as runstore
from ..governance.audit import record_event
from . import auth, ratelimit

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
def start_run(loop_id: str, mode: str, owner: str) -> dict:
    d = _entry_dir(loop_id)
    if d is None:
        return {"error": f"unknown loop {loop_id}"}
    loop_md, skill_md, trace = d / "loop.md", d / "SKILL.md", d / "trace.json"
    if mode == "simulate":
        rec = runstore.create(loop_id=loop_id, owner=owner, loop_path=str(loop_md),
                              skill_path=str(skill_md), trace_path=str(trace),
                              mode="simulate", status=runstore.RUNNING)
        receipt = run_loop(loop_md, skill_path=skill_md, executor=_simulate_executor, ts=_now())
        runstore.finish(rec, receipt)
        return {"run_id": rec.run_id, "status": rec.status, "result": rec.result}
    if mode == "live":
        # Pending: nothing runs until approval.
        rec = runstore.create(loop_id=loop_id, owner=owner, loop_path=str(loop_md),
                              skill_path=str(skill_md), trace_path=str(trace),
                              mode="live", status=runstore.PENDING)
        return {"run_id": rec.run_id, "status": rec.status,
                "result": "Approval required", "needs_approval": True}
    return {"error": f"unknown mode {mode}"}


def approve_run(run_id: str, user: str) -> dict:
    rec = runstore.get(run_id)
    if rec is None:
        return {"error": f"unknown run {run_id}"}
    if rec.owner != user:
        return {"error": "forbidden: not your run"}
    if rec.status != runstore.PENDING:
        return {"error": f"run {run_id} is not pending (status {rec.status})"}
    record_event(actor=user, kind="approval.granted", subject=rec.loop_id,
                 detail={"run_id": rec.run_id})
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


# ──────────────────────────── auth wiring ──────────────────────────────────
# Real auth lives in auth.py (OAuth/dev/token/open + signed sessions). Here we
# just render a login page for the token/dev flows and a button for OAuth.
LOGIN_PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1"><title>ForgeLoop — sign in</title>
<style>body{font:14px/1.6 system-ui,sans-serif;display:grid;place-items:center;height:100vh;margin:0;background:#0d1117;color:#e6edf3}
form{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:28px 32px;width:300px}
h1{font-size:16px;margin:0 0 14px}input{width:100%;box-sizing:border-box;padding:8px;border-radius:6px;
border:1px solid #30363d;background:#0d1117;color:#e6edf3;margin-bottom:12px}
button,a.btn{display:block;text-align:center;text-decoration:none;width:100%;box-sizing:border-box;
padding:9px;border:0;border-radius:6px;background:#1f6feb;color:#fff;font:inherit;cursor:pointer}
.err{color:#f85149;font-size:12px;margin-bottom:8px}</style></head>
<body>%%BODY%%</body></html>"""


def _login_html(err: str = "", m: str | None = None) -> str:
    m = m or auth.mode()
    if m == "oauth":
        body = ('<form><h1>ForgeLoop — sign in</h1>' + err
                + '<a class=btn href="/auth/login">Sign in with GitHub</a></form>')
    else:
        field = ('<input name=user placeholder="Username (dev login)" autofocus>' if m == "dev"
                 else '<input type=password name=token placeholder="Access token" autofocus>')
        body = ('<form method=post action=/login><h1>ForgeLoop — sign in</h1>'
                + err + field + '<button type=submit>Enter</button></form>')
    # .replace, not .format — the CSS contains literal { } braces.
    return LOGIN_PAGE.replace("%%BODY%%", body)


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

    def _html(self, text, code=200, headers: dict | None = None):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    # -- helpers -------------------------------------------------------------
    def _redirect(self, location: str, cookies: list | None = None):
        self.send_response(302)
        self.send_header("Location", location)
        for c in (cookies or []):
            self.send_header("Set-Cookie", c)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _set_session(self, user: str, location: str = "/"):
        record_event(actor=user, kind="auth.login", subject=user, detail={"mode": auth.mode()})
        self._redirect(location, [auth.secure_cookie(self, auth.SESSION_COOKIE,
                                                     auth.make_session(user))])

    def _require(self, p: str) -> str | None:
        """Return the user, or None after writing a 401/login response."""
        user = auth.current_user(self)
        if user:
            return user
        if p.startswith("/api/"):
            self._json({"error": "unauthorized"}, 401)
        else:
            self._html(_login_html(), 401)
        return None

    # -- routes --------------------------------------------------------------
    def do_GET(self):  # noqa: N802
        p = self.path.split("?")[0]
        if p == "/healthz":
            return self._json({"ok": True})
        if p == "/auth/login":
            m = auth.mode()
            if m == "oauth":
                url, state = auth.oauth_authorize_url(self)
                return self._redirect(url, [auth.secure_cookie(self, auth.STATE_COOKIE, state, 600)])
            if m == "open":
                return self._set_session("local")
            return self._html(_login_html())                 # token/dev form
        if p == "/auth/callback":
            return self._auth_callback()
        if p == "/logout":
            u = auth.current_user(self) or "?"
            record_event(actor=u, kind="auth.logout", subject=u)
            return self._redirect("/login", [auth.clear_cookie(auth.SESSION_COOKIE),
                                             auth.clear_cookie("fl_token")])
        if p == "/login":
            return self._redirect("/") if auth.current_user(self) else self._html(_login_html())

        user = self._require(p)
        if not user:
            return
        if p in ("/", "/index.html"):
            return self._html(PAGE)
        if p == "/api/me":
            return self._json({"user": user, "mode": auth.mode()})
        if p == "/api/catalog":
            return self._json(catalog_mod.to_dicts(catalog_mod.build_catalog(EXAMPLES)))
        if p == "/api/runs":
            return self._json([_run_brief(r) for r in runstore.list_runs(owner=user)])
        if p.startswith("/api/runs/"):
            rec = runstore.get(p.rsplit("/", 1)[-1])
            if not rec or rec.owner != user:
                return self._json({"error": "not found"}, 404)
            return self._json(rec.__dict__)
        return self._json({"error": "not found"}, 404)

    def _auth_callback(self):
        q = parse_qs(urlparse(self.path).query)
        code, state = q.get("code", [""])[0], q.get("state", [""])[0]
        if not code or not state or state != auth._cookie(self, auth.STATE_COOKIE):
            return self._html(_login_html('<div class=err>Sign-in state mismatch.</div>'), 400)
        login = auth.oauth_exchange(self, code)
        if not login:
            return self._html(_login_html('<div class=err>Sign-in failed or not allowed.</div>'), 403)
        return self._set_session(login)

    def do_POST(self):  # noqa: N802
        p = self.path.split("?")[0]
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b""

        if p == "/login":
            return self._do_login(raw)

        user = auth.current_user(self)
        if not user:
            return self._json({"error": "unauthorized"}, 401)
        action = "run" if p.endswith("/run") else ("approve" if p.endswith("/approve") else "")
        if action and not ratelimit.allow(f"{user}:{action}"):
            record_event(actor=user, kind="ratelimit.blocked", subject=action)
            return self._json({"error": "rate limited — slow down and retry"}, 429)

        body = json.loads(raw or b"{}") if raw else {}
        if p.startswith("/api/loops/") and p.endswith("/run"):
            loop_id = p[len("/api/loops/"):-len("/run")]
            return self._json(start_run(loop_id, body.get("mode", "simulate"), user))
        if p.startswith("/api/runs/") and p.endswith("/approve"):
            run_id = p[len("/api/runs/"):-len("/approve")]
            return self._json(approve_run(run_id, user))
        return self._json({"error": "not found"}, 404)

    def _do_login(self, raw: bytes):
        m = auth.mode()
        sub = parse_qs(raw.decode())
        if m == "token":
            tok = os.environ.get("FORGELOOP_TOKEN", "")
            if tok and sub.get("token", [""])[0] == tok:
                return self._set_session("shared")
            return self._html(_login_html('<div class=err>Wrong token.</div>'), 401)
        if m == "dev":
            u = re.sub(r"[^A-Za-z0-9_.-]", "", (sub.get("user", [""])[0] or "").strip())[:40]
            if u:
                return self._set_session(u)
            return self._html(_login_html('<div class=err>Enter a username.</div>'), 401)
        return self._redirect("/")   # open / oauth: no form login


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
 header .who{color:#9da7b1;font-size:13px}header .who a{color:#58a6ff;text-decoration:none}
</style></head><body>
<header style="display:flex;justify-content:space-between;align-items:center">
 <div><h1>ForgeLoop</h1><p>Forge skills → governed Loopy loops → runs, in your browser</p></div>
 <div class=who id=who></div></header>
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
async function whoami(){try{const me=await j('/api/me');
 document.getElementById('who').innerHTML=`signed in as <b>${me.user}</b> · ${me.mode} · <a href="/logout">logout</a>`}catch(e){}}
async function refresh(){await whoami();await loadCat();await loadRuns()}
refresh();
</script></body></html>"""
