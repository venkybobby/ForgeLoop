# Hosted recorder — capture skills from clients' browsers

This turns the local "Journey Forge" recorder into a **hosted, multi-tenant**
service: clients install the browser extension, point it at *your* server (or you
bake the URL in), and their recordings flow to your cloud and distil into skills.

```
[client Chrome/Edge + extension]  ──HTTPS──▶  [hosted Forge recorder]  ──distil──▶ skills
                                               fly app, per-client API keys
```

> This is a **separate** Fly app from the ForgeLoop web control plane. The web app
> *runs* loops; this recorder *captures* them.

## 1. Deploy the recorder to Fly

From the repo root (`Dockerfile.forge` + `fly.forge.toml` are already here):

```bash
# pick a unique app name; edit fly.forge.toml's `app =` or pass --app
fly apps create forge-recorder-venky
fly volumes create forge_data --size 1 --region ams --app forge-recorder-venky
fly secrets set --app forge-recorder-venky \
  JFL_ADMIN_TOKEN="$(openssl rand -hex 24)" \
  SF_LLM_KEY="nvapi-…" SF_LLM_BASE="https://integrate.api.nvidia.com" \
  SF_DISTILL_MODEL="z-ai/glm-5.1" SF_CLASSIFY_MODEL="z-ai/glm-5.1"
fly deploy --config fly.forge.toml --app forge-recorder-venky
```

Your recorder is now at `https://forge-recorder-venky.fly.dev`. Check it:
`curl https://forge-recorder-venky.fly.dev/healthz` → `{"ok":true,"keys":0}`.

**Hosting hardening baked in** (see `integration/recorder/serve.py`): binds
`0.0.0.0`, **never seeds the insecure default key**, and **blocks the local-only
routes** (`/api/desktop/*`, `/api/ext/open*`, `/api/codex/*`) that shell out.

## 2. Issue a per-client API key

Each client gets their own key (gated by `JFL_ADMIN_TOKEN`):

```bash
curl -X POST https://forge-recorder-venky.fly.dev/admin/keys \
  -H "X-Admin-Token: <your JFL_ADMIN_TOKEN>"
# -> { "api_key": "fk_XXudY...", "label": "" }

curl https://forge-recorder-venky.fly.dev/admin/keys -H "X-Admin-Token: …"   # list (masked)
curl -X DELETE https://forge-recorder-venky.fly.dev/admin/keys/fk_XXudY... -H "X-Admin-Token: …"  # revoke
```

Give the `fk_…` key to that client (or paste it into their extension Settings).

## 3. Point the extension at your server

The extension's `host_permissions` is `<all_urls>`, so **no per-client rebuild is
needed** — two options:

**a) Client enters it in Settings** (zero build): open the extension popup →
Settings → set **Endpoint** = `https://forge-recorder-venky.fly.dev`, **API key**
= their `fk_…`.

**b) Bake your URL as the default** (so it's pre-filled). Build the extension with:

```bash
cd forge/extension
set WXT_FORGE_ENDPOINT=https://forge-recorder-venky.fly.dev   # (Windows: set; macOS/Linux: export)
pnpm install && pnpm build        # output: forge/extension/dist/chrome-mv3
```

Load it via `chrome://extensions` / `edge://extensions` → Developer mode → **Load
unpacked** → `forge/extension/dist/chrome-mv3`. Record on SARO (or any site) →
finalize → it distils server-side into a `SKILL.md`.

## 4. Publish to the Chrome Web Store / Edge Add-ons (so clients 1-click install)

You do this with **your** developer account (I can't from here):

1. **Build a production zip:** `cd forge/extension && pnpm build && pnpm zip`
   (WXT produces a store-ready zip under `.output/`).
2. **Chrome Web Store:** [chrome.google.com/webstore/devconsole](https://chrome.google.com/webstore/devconsole)
   — one-time **$5** dev fee → *New item* → upload the zip → fill listing (name,
   description, icons, screenshots, privacy policy) → submit (review ~1–3 days).
3. **Edge Add-ons:** [partner.microsoft.com/dashboard/microsoftedge](https://partner.microsoft.com/dashboard/microsoftedge)
   — free → upload the same zip → submit.
4. For **pilots before review**, share the unpacked `dist/chrome-mv3` folder or use
   an enterprise **`ExtensionInstallForcelist`** policy to push it to client machines.

> Update `name`/`description` in `forge/extension/wxt.config.ts` (currently
> "Journey Forge Local") to your product branding before publishing.

## Security & multi-tenancy notes

- **Keep `JFL_ADMIN_TOKEN` secret** — it mints client keys. Rotate with
  `fly secrets set`. HTTPS is enforced (`force_https`).
- **Per-client data isolation is enforced.** Each API key gets its OWN Forge
  server instance bound to its OWN data dir (`data/tenants/<sha256(key)[:16]>/`),
  so one client can never see another's recordings or distilled skills. An ASGI
  dispatcher (`integration/recorder/serve.py`) routes each request to the right
  instance by its `Bearer` key; the portal, `/healthz` and the admin API stay on
  a shared control app that holds no client data. Installed skills also land
  under each tenant's dir, never the shared `~/.claude/skills`.
  - *Upgrade note:* recordings captured before this change live in the legacy
    shared dir (`data/traces`) and won't appear under a tenant — record fresh
    ones after deploying. *Scale note:* one in-memory server instance per active
    key — fine for pilots/hundreds of keys; for large multi-tenant scale move to
    a single context-scoped store or per-tenant DB.
- Recordings can contain sensitive page content — the extension has a redactor
  (`forge/extension/src/redaction/`); confirm your clients' redaction settings.
- Distillation calls your LLM (`SF_LLM_KEY`); cost scales with recordings.

## CI/CD

To auto-deploy the recorder on merge, add a second job to
`.github/workflows/deploy.yml` running
`flyctl deploy --config fly.forge.toml --remote-only` (same `FLY_API_TOKEN`).
