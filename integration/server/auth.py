"""auth — pluggable authentication for the ForgeLoop web app.

Precedence (first configured wins):
  1. OAuth     — GitHub, when GITHUB_OAUTH_CLIENT_ID + _SECRET are set. Real
                 per-user identity. Optional allowlist via FORGELOOP_ALLOWED_USERS.
  2. dev-login — when FORGELOOP_DEV_LOGIN=1: pick any username (no password).
                 For local testing / demos of per-user scoping. NEVER in prod.
  3. token     — when FORGELOOP_TOKEN is set: one shared secret (single tenant).
  4. open      — nothing set: everyone is user "local" (localhost / behind a VPN).

Sessions are signed cookies (HMAC-SHA256, stdlib) — no session table needed.
Stdlib only (hmac, secrets, urllib).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
import urllib.request

SESSION_COOKIE = "fl_session"
STATE_COOKIE = "fl_oauth_state"
_SESSION_TTL = 7 * 24 * 3600

# Ephemeral fallback secret so sessions work even if the operator forgets to set
# one (they just won't survive a restart). Set FORGELOOP_SESSION_SECRET in prod.
_EPHEMERAL_SECRET = secrets.token_hex(32)


def _secret() -> bytes:
    return os.environ.get("FORGELOOP_SESSION_SECRET", _EPHEMERAL_SECRET).encode()


# ──────────────────────────── mode ─────────────────────────────────────────
def mode() -> str:
    if os.environ.get("GITHUB_OAUTH_CLIENT_ID") and os.environ.get("GITHUB_OAUTH_CLIENT_SECRET"):
        return "oauth"
    if os.environ.get("FORGELOOP_DEV_LOGIN") == "1":
        return "dev"
    if os.environ.get("FORGELOOP_TOKEN"):
        return "token"
    return "open"


def _allowed(login: str) -> bool:
    allow = os.environ.get("FORGELOOP_ALLOWED_USERS", "").strip()
    if not allow:
        return True
    return login.lower() in {u.strip().lower() for u in allow.split(",") if u.strip()}


# ──────────────────────────── signed sessions ──────────────────────────────
def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_session(user: str) -> str:
    payload = _b64e(json.dumps({"u": user, "exp": int(time.time()) + _SESSION_TTL}).encode())
    sig = _b64e(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}"


def read_session(cookie_val: str | None) -> str | None:
    if not cookie_val or "." not in cookie_val:
        return None
    payload, sig = cookie_val.split(".", 1)
    expected = _b64e(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        data = json.loads(_b64d(payload))
    except Exception:  # noqa: BLE001
        return None
    if data.get("exp", 0) < time.time():
        return None
    return data.get("u")


# ──────────────────────────── request helpers ──────────────────────────────
def _cookie(handler, name: str) -> str | None:
    import re
    m = re.search(rf"(?:^|;\s*){re.escape(name)}=([^;]+)", handler.headers.get("Cookie", ""))
    return m.group(1) if m else None


def current_user(handler) -> str | None:
    """The authenticated user for this request, or None."""
    m = mode()
    if m == "open":
        return "local"
    # A valid signed session works in every mode.
    u = read_session(_cookie(handler, SESSION_COOKIE))
    if u:
        return u
    if m == "token":
        # Accept the raw token (header/query/legacy cookie) as the shared user.
        tok = os.environ.get("FORGELOOP_TOKEN", "")
        q = urllib.parse.parse_qs(urllib.parse.urlparse(handler.path).query)
        if (handler.headers.get("X-ForgeLoop-Token") == tok
                or q.get("token", [""])[0] == tok
                or _cookie(handler, "fl_token") == tok):
            return "shared"
    return None


def secure_cookie(handler, name: str, value: str, max_age: int = _SESSION_TTL) -> str:
    secure = "; Secure" if handler.headers.get("X-Forwarded-Proto") == "https" else ""
    return f"{name}={value}; HttpOnly; SameSite=Lax; Path=/; Max-Age={max_age}{secure}"


def clear_cookie(name: str) -> str:
    return f"{name}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"


# ──────────────────────────── GitHub OAuth ─────────────────────────────────
def _base_url(handler) -> str:
    env = os.environ.get("FORGELOOP_BASE_URL")
    if env:
        return env.rstrip("/")
    proto = handler.headers.get("X-Forwarded-Proto", "http")
    host = handler.headers.get("Host", "localhost")
    return f"{proto}://{host}"


def oauth_authorize_url(handler) -> tuple[str, str]:
    """Return (redirect_url, state). Caller sets the state cookie."""
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": os.environ["GITHUB_OAUTH_CLIENT_ID"],
        "redirect_uri": f"{_base_url(handler)}/auth/callback",
        "scope": "read:user",
        "state": state,
    }
    return "https://github.com/login/oauth/authorize?" + urllib.parse.urlencode(params), state


def oauth_exchange(handler, code: str) -> str | None:
    """Exchange a code for the GitHub login, honoring the allowlist. None on failure."""
    body = urllib.parse.urlencode({
        "client_id": os.environ["GITHUB_OAUTH_CLIENT_ID"],
        "client_secret": os.environ["GITHUB_OAUTH_CLIENT_SECRET"],
        "code": code,
        "redirect_uri": f"{_base_url(handler)}/auth/callback",
    }).encode()
    req = urllib.request.Request(
        "https://github.com/login/oauth/access_token", data=body,
        headers={"Accept": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            token = json.loads(resp.read()).get("access_token")
        if not token:
            return None
        ureq = urllib.request.Request(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}", "User-Agent": "ForgeLoop"})
        with urllib.request.urlopen(ureq, timeout=15) as resp:
            login = json.loads(resp.read()).get("login")
    except Exception:  # noqa: BLE001
        return None
    if login and _allowed(login):
        return login
    return None
