# ForgeLoop architecture

## The one-sentence model

**Forge produces skills; Loopy runs them in loops; the integration layer governs
the handoff.**

## Subsystems

### Forge (`forge/`, from Browser-BC / "Journey Forge Local")
The recording + distillation engine. **Pure Python at runtime.**

- **extension** — a Chrome extension that records a browser workflow (clicks,
  navigations, inputs) as the user performs it; free-form, points at localhost.
  Built with pnpm to `extension/dist/chrome-mv3`.
- **server** (`server/server.py`) — a local FastAPI ingestion + control API on
  port **8099**. Receives recordings (`/v1/traces/init → chunks → finalize`),
  assembles them to `data/traces/<id>/trace.json`, and exposes `/api/buckets`.
- **harness** (`harness/`, CLI `harness/main.py`) — the distillation pipeline:
  **atomize → classify → bucket → distill → install**. Each recording is split
  into segments, each segment classified into a capability, segments of the same
  capability pooled per domain into a bucket, and each bucket distilled into one
  `SKILL.md` (+ `TRACE_GUIDE.md`).
- **app** (`app/dist/index.html`) — a zero-build control panel served by the
  server (recordings, buckets, skills, browser-execution config).
- **entry** (`entry/main.py`) — desktop entry point (starts server, opens panel).

The harness's output, `SKILL.md`, is the contract between Forge and the rest of
ForgeLoop. It lands under `forge/data/harness/skills/<domain>/<capability>/`.

### Loopy (`loopy/`, from loopy)
The loop runtime / library.

- **loop-library** — the catalog of loops and their logic, plus an optional
  Cloudflare `worker/` (Node) and a docs `site/`.
- **skills** — the agent-facing Loopy skills (`skills/loopy/`, `skills/loop-library/`):
  define a clear goal, then iterate until it's met.

### Integration (`integration/`, new code)
The glue. See [integration/README.md](../integration/README.md). Modules: `core`
(orchestration), `dashboard` (UI), `governance` (audit/traces/approvals), `cli`.

## Why `forge/` and `loopy/` are committed in-tree

The scaffold originally **vendored** these directories on demand (gitignored, with
`scripts/vendor.sh` cloning the upstream forks at setup). That kept upstream
history out of ForgeLoop, but it has a fatal flaw for this project: in an
**access-scoped environment** (the ForgeLoop web environment is scoped to the
`forgeloop` repo) the upstream forks can't be cloned, so `forge/` and `loopy/`
stay empty and **nothing is runnable** — exactly the state Inner Loop 1 must
escape.

So both directories are now **committed in-tree**. The upstream repos are small
(~1.3 MB / ~0.9 MB, no build artifacts), and committing them makes ForgeLoop
self-contained and runnable anywhere, including CI and the scoped web environment.
`scripts/vendor.sh` is retained as an **optional** way to refresh the committed
code from upstream (review the diff, commit deliberately); pin a version with
`FORGE_REF` / `LOOPY_REF`.

Runtime state the subsystems generate (`forge/data/`, `forge/.env.local`,
`forge/extension/dist/`, worker `node_modules/`) is gitignored.

## The SKILL.md contract

Pinned from the real distiller (`forge/harness/distiller.py`). Each distilled
**bucket** (`<domain>::<capability>`) is written to
`forge/data/harness/skills/<domain>/<capability>/` as four files:

| File | Content |
|---|---|
| `SKILL.md` | the distilled skill markdown (the `skill_md` field) — the contract `integration/core` consumes |
| `TRACE_GUIDE.md` | a state-card navigation guide (`trace_guide_md`) |
| `meta.json` | `{ model, usage, segment_count, domains[], distill_version, distilled_at }` |
| `evidence.jsonl` | one row per source segment (`segment_id, source_track, domain, capacity, outcome`) |

The distill LLM call returns a JSON object the harness maps onto a
`DistilledSkill`:

```jsonc
{
  "skill_name": "Human Readable Name",
  "scope": "one sentence: when to use this skill",
  "preconditions": ["..."],
  "milestones": ["..."],
  "terminal_conditions": ["..."],       // how you know you succeeded
  "false_terminal_states": ["..."],     // looks done but isn't
  "recovery_policies": ["..."],         // failure modes + recovery
  "anti_drift_boundaries": ["..."],     // similar actions that are NOT this capability
  "red_lines": ["..."],                 // rules that must never be violated
  "skill_md": "# Skill: ...\n...",      // full markdown body
  "trace_guide_md": "# TRACE GUIDE: ...\n..."
}
```

Two contract guarantees the distill prompt enforces, which `integration/core` and
the quality checklist rely on:

- **Site-agnostic.** The prompt instructs the model to *generalize away
  site-specific selectors and IDs* so one skill applies to any site demonstrating
  the capability — not only the recorded domains.
- **Incremental.** Re-distilling a bucket that already has a `SKILL.md` feeds the
  prior version back in (`INCREMENTAL_ADDENDUM`): keep still-correct rules, drop
  contradicted ones, add newly observed milestones/recoveries/red-lines. This is
  the per-skill inner loop — quality improves as more recordings of the same
  capability arrive (gated by `SF_MIN_BUCKET_SIZE`).

`integration/core` parses `SKILL.md` (plus the sibling `meta.json`) into a
normalized `Skill` (id = `<domain>::<capability>`, `skill_name`, `scope`, the
structured lists above, provenance from `meta.json`). A worked example input lives
at [`examples/login-flow/`](../examples/login-flow/).

## Known constraints

- **Skills don't grant tools.** A `SKILL.md` is injected instructions; executing
  its steps in a browser still requires a browser MCP (Playwright) configured
  separately. The Forge panel automates this for Claude Desktop.
- **LLM access.** Distillation calls the configured LLM (`SF_LLM_KEY` in
  `forge/.env.local`, default Anthropic `claude-opus-4-8`). Nothing else leaves
  the machine.
