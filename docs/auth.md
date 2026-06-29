# Auth, multi-user scoping & rate limits

The web app (`forgeloop serve` / `integration.server`) supports four auth modes.
**Precedence: OAuth → dev-login → token → open** (the first one configured wins).
Sessions are signed cookies (HMAC-SHA256) — no session table needed.

| Mode | Enable with | Identity | Use for |
|---|---|---|---|
| **OAuth** | `GITHUB_OAUTH_CLIENT_ID` + `GITHUB_OAUTH_CLIENT_SECRET` | real GitHub login | teams / multi-user |
| **dev-login** | `FORGELOOP_DEV_LOGIN=1` | any typed username (no password) | local testing of scoping |
| **token** | `FORGELOOP_TOKEN=…` | shared user `shared` | solo / single-tenant |
| **open** | (nothing set) | `local` | localhost / behind a VPN |

`/healthz` is always public (for platform health checks).

## Per-user run scoping

Every run record has an **owner**. Each user sees and controls only their own
runs:

- `GET /api/runs` lists only the caller's runs.
- `GET /api/runs/<id>` returns 404 for runs you don't own.
- `POST /api/runs/<id>/approve` returns *"forbidden: not your run"* otherwise.

In **token**/**open** mode there's effectively one user (`shared`/`local`), so the
runs are shared — scoping only differentiates real users (OAuth/dev).

## Rate limits

`FORGELOOP_RATE_PER_MIN` (default **30**, `0` = off) caps `run` + `approve` calls
per user per minute. Over the limit → HTTP **429** and a `ratelimit.blocked` audit
event.

## Storage

Audit trail + run records are one SQLite file at `FORGELOOP_DB`
(default `./.data/forgeloop.db`, gitignored). It survives restarts; mount it on a
volume in production (the Fly config already does).

## Set up GitHub OAuth

1. GitHub → **Settings → Developer settings → OAuth Apps → New OAuth App**.
2. **Homepage URL:** `https://<your-app>` · **Authorization callback URL:**
   `https://<your-app>/auth/callback`.
3. Copy the **Client ID** + generate a **Client secret**.
4. Configure the app:
   ```bash
   # Fly:
   fly secrets set GITHUB_OAUTH_CLIENT_ID=… GITHUB_OAUTH_CLIENT_SECRET=… \
                   FORGELOOP_BASE_URL=https://<your-app>.fly.dev \
                   FORGELOOP_SESSION_SECRET="$(openssl rand -hex 32)" \
                   FORGELOOP_ALLOWED_USERS=you,teammate
   ```
   `FORGELOOP_BASE_URL` must match the callback's origin. `FORGELOOP_ALLOWED_USERS`
   (optional) restricts sign-in to those GitHub logins.

> Always set `FORGELOOP_SESSION_SECRET` in production — without it, a random
> per-process secret is used and everyone is logged out on each restart/redeploy.

## Quick local test (dev-login)

```bash
FORGELOOP_DEV_LOGIN=1 python -m integration.cli.forgeloop serve
# open http://127.0.0.1:8055/ → type a username → you're "signed in" as that user.
```
