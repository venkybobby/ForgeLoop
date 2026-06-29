# ForgeLoop

**ForgeLoop** integrates two tools into a single, self-hosted, loop-engineered product:

- **Forge** ([Browser-BC](https://github.com/venkybobby/Browser-BC)) — record a browser workflow and **distill** it into a clean, reusable `SKILL.md`.
- **Loopy** ([loopy](https://github.com/venkybobby/loopy)) — a **loop library** and agent skill that runs structured loops (define a clear goal → iterate until the goal is met).

The thesis: **Forge produces skills, Loopy runs them in loops.** ForgeLoop is the glue that turns a recorded browser session into a governed, repeatable, agent-driven loop.

```
record (Forge extension)
        │
        ▼
ingest (Forge server)
        │
        ▼
distill (Forge harness)  ──►  SKILL.md
        │
        ▼
register (integration)   ──►  catalog
        │
        ▼
run (Loopy loop)         ──►  governed runs + traces
```

## Repository layout

```
ForgeLoop/
├── forge/          # From Browser-BC — recording + distillation (pure Python runtime)
│   ├── extension/  #   Chrome extension (recording)
│   ├── server/     #   FastAPI ingestion + control API (port 8099)
│   ├── harness/    #   Distillation pipeline (atomize → classify → bucket → distill)
│   ├── app/        #   Zero-build control panel (served by the server)
│   ├── entry/      #   Desktop entry point
│   └── docs/
├── loopy/          # From loopy — loop library + agent skills
│   ├── loop-library/  # Loop catalog + logic (+ optional Cloudflare worker)
│   ├── skills/        # Loopy agent skills
│   └── ...
├── integration/    # New code — the glue layer (most development happens here)
│   ├── core/       #   Orchestration: skill → catalog → loop
│   ├── dashboard/  #   Web UI (skills + loops + runs)
│   ├── governance/ #   Audit logs, traces, approval gates
│   └── cli/        #   Command-line tools
├── examples/       # Example workflows and loops
├── scripts/        # Setup, vendor, build, deploy
├── docs/           # Overall documentation
├── docker-compose.yml
├── .env.example
└── README.md
```

> **`forge/` and `loopy/` are committed in-tree** so ForgeLoop is self-contained
> and runnable anywhere (including the access-scoped web environment). The upstream
> code is small and carries no build artifacts. `scripts/vendor.sh` is an optional
> way to refresh it from upstream. See [docs/architecture.md](docs/architecture.md)
> for the rationale.

## Quick start

```bash
# 1. Install deps + config for both subsystems (forge/ and loopy/ are already present)
./scripts/bootstrap.sh

# 2. Set your LLM key for distillation
#    forge/.env.local  →  SF_LLM_KEY=sk-ant-...

# 3. Start Forge (server + control panel on http://127.0.0.1:8099)
( cd forge && ./scripts/start.sh )
```

Then follow [docs/forge-setup.md](docs/forge-setup.md) to record your first
workflow and produce a `SKILL.md`.

## Loop engineering

ForgeLoop is built **with** the same method it ships: define a clear final goal,
then run structured loops until the goal is achieved. The current development loop
is **Inner Loop 1** — see [docs/loop-engineering.md](docs/loop-engineering.md) for
the goal, success criteria, and step plan.

## Status

✅ **Inner Loops 1–3 complete + a browser-deployable web app** — record → distill →
govern → **run for real**, all usable from a browser.

- **Loop 1 (Forge):** code committed in-tree; two workflows distilled into clean,
  site-agnostic `SKILL.md` files.
- **Loop 2 (integration):** a distilled `SKILL.md` is bound into a governed Loopy
  `loop.md` and run in bounded passes with an **approval gate**, producing a
  Loopy-format **receipt** + an **audit trail**.
- **Loop 3 (real execution):** an *approved* run drives a **real browser**
  (Playwright) and reaches a real terminal state from live page content.

```bash
# skill -> governed loop -> bounded run -> receipt
python -m integration.cli.forgeloop bind examples/form-fill/SKILL.md --out examples/form-fill/loop.md
python -m integration.cli.forgeloop run  examples/form-fill/loop.md --skill examples/form-fill/SKILL.md
python -m integration.cli.forgeloop status

# real browser run (mandatory approval; replays the recording against a live page)
python -m pip install -r integration/requirements.txt
python scripts/live_demo.py          # form-fill -> Result: Success (+ screenshot)
```

Both examples run live to `Success` (`python scripts/live_demo.py {form-fill|login-flow}`).
Browse everything:

```bash
python -m integration.cli.forgeloop catalog       # bound loops + latest run result
python -m integration.cli.forgeloop dashboard      # static integration/dashboard/index.html
```

See [`examples/form-fill/`](examples/form-fill/) and
[`examples/login-flow/`](examples/login-flow/) — each has `loop.md`, `RECEIPT.md`
(approval gate), `RECEIPT.live.md` (real `Success` run), and a screenshot.

## Use it in your browser

ForgeLoop ships a **web control plane** — bind, run, **approve live runs**, and read
receipts from any browser. One command to deploy:

```bash
docker compose up forgeloop-web        # then open http://localhost:8055/
# or, without Docker:
python -m integration.cli.forgeloop serve
```

In the UI: **Catalog** → **Simulate** (safe dry-run) or **Run live** → **Approve &
run** (the governance gate) → **Receipt**. Guides: [docs/deploy.md](docs/deploy.md)
· **[Fly.io (cheap, scale-to-zero)](docs/deploy-fly.md)**. Set `FORGELOOP_TOKEN` to
gate the URL with a login.

**Execution modes:** *replay* a recording (`scripts/live_demo.py`) or *agentic* —
an LLM chooses each action against the live DOM (`scripts/agentic_demo.py`; set
`SF_LLM_KEY` for autonomy).

> **Sandbox note:** this environment blocks public network egress, so the bundled
> examples run against a local copy of their target page; the mechanism is identical
> for a reachable public site (only the URL changes).

▶️ **Remaining (hardening, not features):** API auth + HTTPS before exposing beyond
localhost, per-user scoping, and live agentic runs against public sites (needs
egress). See [docs/loop-engineering.md](docs/loop-engineering.md).
