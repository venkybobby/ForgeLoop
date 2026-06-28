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
├── forge/          # Vendored from Browser-BC — recording + distillation
│   ├── extension/  #   Chrome extension (recording)
│   ├── server/     #   Ingestion server
│   ├── harness/    #   Distillation pipeline (atomize → classify → bucket → distill)
│   ├── app/        #   Control panel
│   └── docs/
├── loopy/          # Vendored from loopy — loop management
│   ├── loop-library/  # Loop catalog + logic
│   ├── skill/         # Loopy skill for agents
│   └── docs/
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

> **`forge/` and `loopy/` are vendored, not committed.** Their contents are pulled
> from the upstream forks by `scripts/vendor.sh`. Only a `README.md` placeholder is
> tracked in each. See [docs/architecture.md](docs/architecture.md) for why.

## Quick start

```bash
# 1. Pull the upstream Forge + Loopy code into forge/ and loopy/
./scripts/vendor.sh

# 2. Create your .env from the template and fill in the blanks
cp .env.example .env

# 3. Install dependencies for both subsystems
./scripts/setup-forge.sh
./scripts/setup-loopy.sh

# 4. (or do all of the above in one shot)
./scripts/bootstrap.sh
```

Then follow [docs/forge-setup.md](docs/forge-setup.md) to record your first
workflow and produce a `SKILL.md`.

## Loop engineering

ForgeLoop is built **with** the same method it ships: define a clear final goal,
then run structured loops until the goal is achieved. The current development loop
is **Inner Loop 1** — see [docs/loop-engineering.md](docs/loop-engineering.md) for
the goal, success criteria, and step plan.

## Status

🚧 **Early scaffold.** The repo structure, glue-layer skeleton, setup scripts, and
docs are in place. The upstream `forge/` and `loopy/` code is vendored on demand and
is **not** yet validated end-to-end inside ForgeLoop (Inner Loop 1, Step 4 onward).
See [docs/loop-engineering.md](docs/loop-engineering.md) for what's done and what's next.
