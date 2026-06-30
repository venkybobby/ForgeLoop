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
from fastapi.responses import JSONResponse  # noqa: E402


@app.middleware("http")
async def _block_local_routes(request, call_next):
    if any(request.url.path.startswith(b) for b in BLOCKED_PREFIXES):
        return JSONResponse({"detail": "endpoint disabled on the hosted server"}, status_code=403)
    return await call_next(request)


@app.get("/healthz")
def _healthz():
    return {"ok": True, "keys": len(_keys())}


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


# The vendored server mounts the control-panel SPA at "/" as a catch-all
# (StaticFiles). Routes registered after a catch-all are never reached, so move
# ours to the FRONT of the router to be matched first.
_OURS = {"/healthz", "/admin/keys", "/admin/keys/{key}"}
_mine = [r for r in app.router.routes if getattr(r, "path", None) in _OURS]
for r in _mine:
    app.router.routes.remove(r)
for r in reversed(_mine):
    app.router.routes.insert(0, r)


def main() -> None:
    import uvicorn
    port = int(os.environ.get("PORT", os.environ.get("JFL_PORT", "8099")))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
