"""serve — hosted, multi-tenant Forge ingestion server.

Wraps the vendored Forge server (forge/server/server.py) so it can run safely on
the internet and receive recordings from many clients' browser extensions:

- binds 0.0.0.0:$PORT (the vendored server binds 127.0.0.1, localhost-only);
- BLOCKS the local-only / subprocess routes (open Chrome, install Node, reveal a
  folder, edit Codex config) — dangerous on a shared host;
- multi-tenant API keys: seed from $JFL_API_KEYS, and issue / list / revoke
  per-client keys via an admin API (gated by $JFL_ADMIN_TOKEN);
- never auto-seeds the insecure default `jfl-local-dev-key` on a host;
- adds /healthz for platform checks.

The recording protocol (/v1/traces/init → chunks → finalize) and distillation
(needs $SF_LLM_KEY) come straight from the vendored server unchanged.

Run:  python -m integration.recorder.serve
"""

from __future__ import annotations

import importlib.util
import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORGE = ROOT / "forge"
DATA = Path(os.environ.setdefault("JFL_DATA_DIR", str(FORGE / "data")))
KEYS_FILE = DATA / "api-keys.json"

# Local-only routes that shell out or are desktop-specific — refused when hosted.
BLOCKED_PREFIXES = ("/api/desktop", "/api/codex", "/api/ext/open", "/api/ext/reveal")


def _seed_keys() -> None:
    """Write api-keys.json from $JFL_API_KEYS; otherwise ensure it exists EMPTY so
    the vendored server never auto-seeds the insecure default key on a host."""
    DATA.mkdir(parents=True, exist_ok=True)
    env_keys = [k.strip() for k in os.environ.get("JFL_API_KEYS", "").split(",") if k.strip()]
    if env_keys:
        KEYS_FILE.write_text(json.dumps(sorted(set(env_keys)), indent=2))
    elif not KEYS_FILE.exists():
        KEYS_FILE.write_text("[]")


def _load_forge_app():
    spec = importlib.util.spec_from_file_location("jfl_server", FORGE / "server" / "server.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["jfl_server"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.app


_seed_keys()
app = _load_forge_app()

from fastapi import Header, HTTPException  # noqa: E402  (fastapi is imported by the server)
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: E402


@app.middleware("http")
async def _block_local_routes(request, call_next):
    if any(request.url.path.startswith(b) for b in BLOCKED_PREFIXES):
        return JSONResponse({"detail": "endpoint disabled on the hosted server"}, status_code=403)
    return await call_next(request)


@app.get("/healthz")
def _healthz():
    return {"ok": True, "keys": len(_keys())}


# ──────────────────────────── skills portal (browser UI) ───────────────────
@app.get("/", response_class=HTMLResponse)
@app.get("/portal", response_class=HTMLResponse)
def _portal():
    return HTMLResponse(PORTAL_HTML)


# ──────────────────────────── admin key management ─────────────────────────
def _admin_token() -> str:
    return os.environ.get("JFL_ADMIN_TOKEN", "")


def _check_admin(token: str | None) -> None:
    if not _admin_token() or token != _admin_token():
        raise HTTPException(403, "missing or invalid X-Admin-Token")


def _keys() -> list[str]:
    return json.loads(KEYS_FILE.read_text()) if KEYS_FILE.exists() else []


def _write_keys(keys) -> None:
    KEYS_FILE.write_text(json.dumps(sorted(set(keys)), indent=2))


@app.post("/admin/keys")
def create_key(x_admin_token: str | None = Header(None), label: str = ""):
    """Issue a new per-client API key. The client puts it in the extension Settings."""
    _check_admin(x_admin_token)
    new = "fk_" + secrets.token_urlsafe(24)
    _write_keys(_keys() + [new])
    return {"api_key": new, "label": label}


@app.get("/admin/keys")
def list_keys(x_admin_token: str | None = Header(None)):
    _check_admin(x_admin_token)
    ks = _keys()
    return {"count": len(ks), "keys": [f"{k[:6]}…{k[-4:]}" for k in ks]}


@app.delete("/admin/keys/{key}")
def revoke_key(key: str, x_admin_token: str | None = Header(None)):
    _check_admin(x_admin_token)
    remaining = [k for k in _keys() if k != key]
    _write_keys(remaining)
    return {"revoked": key, "remaining": len(remaining)}


# Drop the vendored server's plain "/" JSON route so the portal owns the root.
app.router.routes[:] = [
    r for r in app.router.routes
    if not (getattr(r, "path", None) == "/"
            and getattr(getattr(r, "endpoint", None), "__name__", "") != "_portal")
]
# The vendored server mounts the control-panel SPA at "/" as a catch-all
# (StaticFiles). Routes registered after a catch-all are never reached, so move
# ours to the FRONT of the router to be matched first.
_OURS = {"/", "/portal", "/healthz", "/admin/keys", "/admin/keys/{key}"}
_mine = [r for r in app.router.routes if getattr(r, "path", None) in _OURS]
for r in _mine:
    app.router.routes.remove(r)
for r in reversed(_mine):
    app.router.routes.insert(0, r)


PORTAL_HTML = r"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1"><title>Forge Recorder — Skills</title>
<style>
 body{font:14px/1.55 system-ui,sans-serif;margin:0;background:#f6f8fa;color:#1f2328}
 header{background:#0d1117;color:#fff;padding:14px 22px;display:flex;justify-content:space-between;align-items:center}
 header h1{margin:0;font-size:17px} header .r{font-size:12px;color:#9da7b1}
 header a{color:#58a6ff;text-decoration:none;margin-left:10px;cursor:pointer}
 main{max-width:1000px;margin:22px auto;padding:0 16px}
 h2{font-size:14px;margin:22px 0 8px;text-transform:uppercase;letter-spacing:.04em;color:#57606a}
 table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d0d7de;border-radius:8px;overflow:hidden}
 th,td{text-align:left;padding:8px 12px;border-bottom:1px solid #eaeef2;vertical-align:top;font-size:13px}
 th{background:#f6f8fa;font-size:11px;text-transform:uppercase;color:#57606a}
 code{background:#eff1f3;padding:1px 5px;border-radius:4px;font-size:12px}
 .badge{color:#fff;padding:2px 8px;border-radius:999px;font-size:12px;white-space:nowrap}
 .muted{color:#8b949e;font-size:12px} .link{color:#1f6feb;cursor:pointer;text-decoration:underline}
 button{font:inherit;border:1px solid #d0d7de;background:#fff;border-radius:6px;padding:6px 12px;cursor:pointer}
 button.p{background:#1f6feb;color:#fff;border-color:#1f6feb}
 input{font:inherit;padding:8px;border:1px solid #d0d7de;border-radius:6px;width:340px;max-width:100%}
 .card{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:26px;max-width:420px;margin:12vh auto}
 pre{background:#0d1117;color:#e6edf3;padding:16px;border-radius:8px;overflow:auto;font-size:12.5px;white-space:pre-wrap}
 #skillbox{display:none;margin-top:10px}
</style></head><body>
<div id=login class=card>
  <h1 style="margin:0 0 4px;font-size:18px">Forge Recorder</h1>
  <p class=muted>Enter your API key to view your recordings & skills.</p>
  <p><input id=key type=password placeholder="fk_..." autofocus></p>
  <button class=p onclick="saveKey()">Enter</button>
  <p id=loginerr style="color:#d1242f;font-size:12px"></p>
</div>
<div id=app style=display:none>
 <header><h1>Forge Recorder — Skills</h1>
   <div class=r><span id=stat></span> · <a onclick=refresh()>refresh</a> · <a onclick=logout()>sign out</a></div></header>
 <main>
   <h2>Recordings</h2>
   <table id=rec><thead><tr><th>When</th><th>Label / site</th><th>Status</th><th>Distillation</th></tr></thead><tbody></tbody></table>
   <h2>Skills</h2>
   <table id=sk><thead><tr><th>Skill</th><th>Site</th><th>Segments</th><th>Distilled</th><th></th></tr></thead><tbody></tbody></table>
   <div id=skillbox><h2 id=skilltitle></h2><pre id=skillmd></pre></div>
 </main>
</div>
<script>
const RC={running:'#1a73e8',queued:'#b06000',done:'#137333',error:'#b3261e',accepted:'#1a73e8'};
const badge=t=>t?`<span class=badge style="background:${RC[t]||'#666'}">${t}</span>`:'<span class=muted>—</span>';
function key(){return localStorage.getItem('fk_key')||''}
function hdr(){return {Authorization:'Bearer '+key()}}
async function api(p){const r=await fetch(p,{headers:hdr()});if(r.status===401){logout();throw new Error('unauthorized')}return r.json()}
function saveKey(){const k=document.getElementById('key').value.trim();if(!k)return;localStorage.setItem('fk_key',k);show()}
function logout(){localStorage.removeItem('fk_key');document.getElementById('app').style.display='none';document.getElementById('login').style.display='block'}
async function show(){
  document.getElementById('login').style.display='none';document.getElementById('app').style.display='block';refresh()}
async function loadRec(){const d=await api('/api/traj');
  document.querySelector('#rec tbody').innerHTML=(d.trajectories||[]).map(t=>{
    const pr=t.progress?` <span class=muted>(${t.progress.phase} ${t.progress.current}/${t.progress.total})</span>`:'';
    const note=t.note?`<div class=muted style="margin-top:4px;max-width:340px">${t.note}</div>`:'';
    return `<tr><td class=muted>${(t.created_at||'').replace('T',' ').slice(0,19)}</td>
      <td>${t.label||'<span class=muted>(untitled)</span>'}</td><td>${badge(t.status)}</td>
      <td>${badge(t.distill_status)}${pr}${note}</td></tr>`}).join('')||'<tr><td colspan=4 class=muted>No recordings yet — record one with the extension.</td></tr>'}
async function loadSkills(){const d=await api('/api/buckets');const rows=[];
  (d.domains||[]).forEach(dom=>dom.buckets.forEach(b=>rows.push({dom:dom.domain,...b})));
  document.querySelector('#sk tbody').innerHTML=rows.map(b=>`<tr>
    <td>${b.skill_name||b.capacity||b.bucket_id}<br><span class=muted>${b.scope||''}</span></td>
    <td>${b.dom}</td><td>${b.segments}</td><td>${b.distilled?badge('done'):'<span class=muted>pending</span>'}</td>
    <td>${b.distilled?`<span class=link onclick="viewSkill('${b.bucket_id}')">view</span>`:''}</td></tr>`).join('')
    ||'<tr><td colspan=5 class=muted>No distilled skills yet.</td></tr>'}
async function viewSkill(bid){const d=await api('/api/skill?bucket='+encodeURIComponent(bid));
  document.getElementById('skilltitle').textContent=bid;
  document.getElementById('skillmd').textContent=d.skill_md||'(empty)';
  document.getElementById('skillbox').style.display='block';
  document.getElementById('skillbox').scrollIntoView({behavior:'smooth'})}
async function refresh(){try{document.getElementById('stat').textContent='updating…';
  await Promise.all([loadRec(),loadSkills()]);
  document.getElementById('stat').textContent='updated '+new Date().toLocaleTimeString()}catch(e){}}
if(key()){show()}
setInterval(()=>{if(key())refresh()},5000);
</script></body></html>"""


def main() -> None:
    import uvicorn
    port = int(os.environ.get("PORT", os.environ.get("JFL_PORT", "8099")))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
