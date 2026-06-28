# Loop engineering & ForgeLoop development loops

ForgeLoop is built the way it runs: **define a clear final goal, then run
structured loops until the goal is achieved.** This file is the live log of those
development loops.

## Method

1. **Define the goal** — one sentence, with measurable success criteria.
2. **Plan the steps** — a sequence you can run start-to-finish.
3. **Run the loop** — execute, observe, and on failure adjust one thing and
   re-run.
4. **Lock the loop** — only move on when the success criteria hold twice.

---

## Inner Loop 1 — Forge recording + distillation inside ForgeLoop

**Goal:** Recording a browser workflow inside ForgeLoop produces a clean,
Loopy-ready `SKILL.md`.

### Success criteria

- [x] ForgeLoop repo exists with the agreed structure.
- [x] Forge's extension + server + harness are integrated and runnable. *(code
  committed in-tree, wired to real entrypoints; runs locally with Python + pnpm)*
- [x] A user can record a workflow and get a clean `SKILL.md`. *(live run: login
  trace → `examples/login-flow/SKILL.md`, distilled with `claude-haiku-4-5`)*
- [x] The skill is good enough to be consumed by Loopy. *(passes the full quality
  checklist; site-agnostic; no credentials leaked)*
- [x] Basic setup instructions exist.

### Step status

| # | Step | State | Notes |
|---|------|-------|-------|
| 1 | Create repo + structure | ✅ done | Scaffold, README, structure. |
| 2 | Bring in Forge code | ✅ done | Browser-BC committed to `forge/`, loopy to `loopy/` (135 + 53 files). Blocker resolved — this session has access to all three repos. |
| 3 | Basic integration / setup scripts | ✅ done | `vendor.sh` (now a refresh tool), `setup-forge.sh`, `setup-loopy.sh`, `bootstrap.sh` — rewritten for the **real** Forge (pure-Python server/harness, pnpm extension). |
| 4 | Test recording + distillation | ✅ done | **Live end-to-end run**: `python -m harness.main full --track-file examples/login-flow/trace.json` → 1 track ingested → 1 segment classified (`login-with-credentials`) → 1 bucket → 1 skill distilled (`claude-haiku-4-5`, 635 in / 5329 out). Output in [`examples/login-flow/`](../examples/login-flow/). Server boot + panel + `/api/buckets` also verified. |
| 5 | Quality check + improve prompts | ✅ done | `SKILL.md` passes the full [forge-setup.md](forge-setup.md) checklist (clear goal, atomic ordered steps, concrete-but-generalized selectors, **no leaked credentials**, Loopy-followable). Contract pinned in [architecture.md](architecture.md). Prompt in `forge/harness/distiller.py` if quality needs raising (e.g. re-distill with Opus). |
| 6 | Documentation | ✅ done | `forge-setup.md`, `loopy-setup.md`, `architecture.md`, this file — all corrected to reality. |
| 7 | Debrief + lock loop | 🔶 1 of 2 | First end-to-end run is clean and passes the checklist (login-flow). One more run with a *different* workflow (e.g. form-fill) locks the loop. |

### Blocker — resolved

The prior session's environment was **scoped to `forgeloop` only**, so it could not
clone `Browser-BC` / `loopy` (HTTP 403) and chose to vendor on demand — which left
`forge/` and `loopy/` empty and nothing runnable. **This session's access includes
all three repos**, so the upstream code is now **committed in-tree** (one of the
unblock options the original PR listed). ForgeLoop is now self-contained: a fresh
clone is runnable with no external repo access.

### What worked / what was hard

- _What worked:_ committing the upstream code in-tree (it's small, no build
  artifacts) makes the repo self-contained and immediately runnable; reading the
  real harness/server pinned down the entrypoints the scaffold had only guessed.
- _What was hard:_ the scaffold's docs/scripts assumed a Node-per-subsystem layout
  and port 4000 / `ANTHROPIC_API_KEY`; the real Forge is pure-Python on port 8099
  reading `SF_LLM_KEY` from `forge/.env.local`. All of that was corrected.

### First run debrief (login-flow)

- _What worked:_ the headless path — a hand-authored `human-tracks` `trace.json`
  through `harness.main full` — produced a high-quality, **site-agnostic**
  `SKILL.md` on the cheapest model (`claude-haiku-4-5`, ~6k tokens total). The
  distiller correctly **generalized away the recorded selectors/credentials** (no
  leak), and emitted the full contract (milestones, terminal/false-terminal
  states, recovery, red-lines) plus a `TRACE_GUIDE.md`.
- _What was hard:_ LLM **reachability**, not the code — NVIDIA is egress-blocked
  in the web environment and the first Anthropic key was out of credits. Once a
  funded, allowlisted key was in place, the run was one command.

### Remaining to lock the loop (Step 7)

1. ✅ Run #1: login-flow → clean `SKILL.md` (done, committed).
2. ⏳ Run #2: a *different* workflow (e.g. `examples/form-fill/`) → confirm it also
   passes the [forge-setup.md](forge-setup.md) checklist.
3. Optional: re-distill login-flow with Opus and diff against the Haiku version to
   gauge the quality/cost tradeoff before standardizing a model.

---

## Small loops we'll run inside the big one

- "Improve the distillation prompt until the generated `SKILL.md` passes the
  quality checklist in [forge-setup.md](forge-setup.md)."
- "Make `bootstrap.sh` run clean on a fresh machine with no errors."
