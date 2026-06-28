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

🚧 **Integrating.** Repo structure, glue-layer skeleton, setup scripts, and docs
are in place, and the Forge + Loopy code is now **committed in-tree** and wired to
its real entrypoints (server on 8099, `harness/main.py` distiller, `forge/.env.local`
config). Still pending: a live end-to-end record → distill run (needs an
`SF_LLM_KEY` and an interactive browser) and the Loopy hand-off (Inner Loop 1,
Steps 4–7). See [docs/loop-engineering.md](docs/loop-engineering.md) for the live
status board.
