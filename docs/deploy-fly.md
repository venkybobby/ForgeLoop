# Deploy ForgeLoop to Fly.io (cheap)

The fastest, cheapest way to get a private ForgeLoop URL. Fly builds the Docker
image on its **remote builder** (with internet, so `playwright install` works) —
**you don't need Docker locally**, just `flyctl`.

**Cost shape:** one `shared-cpu-1x` / 1 GB machine that **scales to zero when idle**
(`min_machines_running = 0`) + a 1 GB volume. Idle ≈ the volume only (~$0.15/mo);
you pay for compute only while it's actively running, and it cold-starts in a few
seconds on the next request. (Pay-as-you-go — not strictly free, but cents-level
for light use.)

## 1. One-time setup

```bash
# install flyctl: https://fly.io/docs/flyctl/install/
curl -L https://fly.io/install.sh | sh        # or: brew install flyctl
fly auth login
```

## 2. Create the app + volume

From the repo root (the `fly.toml` is already here):

```bash
# pick a unique app name and your region, then either edit fly.toml's `app`/`primary_region`
# or let launch do it (reuse the existing fly.toml when asked):
fly launch --no-deploy --copy-config --name <your-unique-name> --region <region>

# persistent storage for the audit trail + receipts (same region as the app):
fly volumes create forgeloop_data --size 1 --region <region>
```

## 3. Set secrets (never commit these)

```bash
# protect the public URL with a shared token (you'll enter it on a login page):
fly secrets set FORGELOOP_TOKEN="$(openssl rand -hex 16)"

# LLM key for agentic runs (Fly has open egress, so NVIDIA/Anthropic both work):
fly secrets set SF_LLM_KEY="nvapi-…" \
                SF_LLM_BASE="https://integrate.api.nvidia.com" \
                SF_DISTILL_MODEL="z-ai/glm-5.1" \
                SF_CLASSIFY_MODEL="z-ai/glm-5.1"
```

> The web app reads `SF_LLM_KEY` straight from the environment — no `.env` file
> needed in the container. Replay (`Run live`) needs no key; only **agentic** runs do.

## 4. Deploy

```bash
fly deploy
fly open            # opens https://<app>.fly.dev/  → enter your FORGELOOP_TOKEN
```

## 5. Use it

- Sign in with the token → **Catalog** → **Simulate** or **Run live → Approve & run**
  → **Receipt**.
- `fly logs` to watch; `fly status` for machine state; `fly secrets list` to see
  (names of) configured secrets.

## Cost & ops knobs

| Want | Do |
|---|---|
| Cheapest | keep `min_machines_running = 0` (default here) — scales to zero |
| Always-warm (no cold start) | set `min_machines_running = 1` (costs more) |
| Heavy pages OOM | bump `[[vm]] memory` to `"2gb"` and `fly deploy` |
| Rotate the access token / LLM key | `fly secrets set FORGELOOP_TOKEN=… ` (triggers a restart) |
| Tear down | `fly apps destroy <app>` (and `fly volumes destroy`) |

## Security notes (MVP)

- The `FORGELOOP_TOKEN` gate is a **single shared secret**, not per-user auth — fine
  for private/solo use behind HTTPS. For a team, put it behind **Cloudflare Access**
  or **Tailscale**, or add real OAuth (Phase 2).
- HTTPS is handled by Fly (`force_https = true`). The token cookie is `HttpOnly`,
  `SameSite=Lax`, and `Secure` (set when Fly terminates TLS).
- The **approval gate** still applies: live browser actions need an explicit
  **Approve** click; nothing runs unattended.
