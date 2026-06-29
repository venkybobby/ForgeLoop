# Deploy ForgeLoop in any browser

ForgeLoop ships a self-hosted **web control plane**: a browser UI + JSON API over
the integration layer (catalog, runs, approvals, receipts). Deploy it once and use
the whole product — bind skills to loops, run them, approve live runs, read
receipts — from any browser.

## Option A — Docker (recommended, one command)

```bash
docker compose up forgeloop-web
# then open http://localhost:8055/
```

The image (see [`Dockerfile`](../Dockerfile)) bundles Python + Playwright +
Chromium, so **live runs work out of the box**. The audit trail and run records
persist to `./.data` (mounted volume).

Plain Docker:

```bash
docker build -t forgeloop .
docker run -p 8055:8055 -v "$PWD/.data:/app/.data" forgeloop
```

## Option B — Local Python (no Docker)

```bash
python -m pip install -r integration/requirements.txt   # Playwright (Chromium pre-installed in this env)
python -m integration.cli.forgeloop serve               # or: python -m integration.server
# open http://127.0.0.1:8055/
```

The catalog, dashboard, and **simulate** runs need no third-party deps at all;
only **live**/**agentic** runs use Playwright.

## What you can do in the browser

| Action | How |
|---|---|
| Browse skills/loops + latest result | the **Catalog** table |
| Dry-run a loop safely | **Simulate** button → `Clean no-op` receipt |
| Run for real, with a human in the loop | **Run live** → creates a *pending* run → **Approve & run** → executes the browser → receipt |
| Read the evidence | **Receipt** button (Loopy-format receipt + extracted page text) |

Live runs honour the **approval gate**: nothing touches a browser until you click
**Approve**. Every step is recorded in the governance audit trail.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `DASHBOARD_HOST` / `DASHBOARD_PORT` | `0.0.0.0` / `8055` | where the web app listens |
| `GOVERNANCE_AUDIT_DIR` | `./.data/audit` | append-only audit trail |
| `LOOPY_RUNS_DIR` | `./.data/runs` | persisted run records + receipts |
| `SF_LLM_KEY` / `SF_LLM_BASE` / `SF_DISTILL_MODEL` | — | enable **LLM-driven (agentic)** runs |

## Live vs. agentic execution

- **Live (replay):** replays a recorded `trace.json` against the page — fast and
  deterministic. `scripts/live_demo.py`, or **Run live** in the UI.
- **Agentic (LLM):** the next action is *chosen* by an LLM against the live DOM, so
  it handles pages that differ from the recording. `scripts/agentic_demo.py`
  (set `SF_LLM_KEY` for autonomy; otherwise a scripted chooser stands in).

## Sandbox / egress note

This development environment blocks public network egress, so the bundled examples
run against a **local copy** of their target page (`examples/*/local_server.py`).
In a normal deployment with outbound access, the same loops target the recorded
sites directly — only network reachability changes, not the code.

## Production hardening (not yet done)

This is an MVP control plane. Before exposing it beyond localhost, add: auth on the
API, per-user scoping, HTTPS/reverse-proxy, and rate limits. The approval gate
protects against *unattended* side effects, not against an untrusted network.
