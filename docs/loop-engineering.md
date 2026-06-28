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
- [ ] A user can record a workflow and get a clean `SKILL.md`. *(needs a live
  `SF_LLM_KEY` + an interactive browser — can't be exercised headlessly here)*
- [ ] The skill is good enough to be consumed by Loopy.
- [x] Basic setup instructions exist.

### Step status

| # | Step | State | Notes |
|---|------|-------|-------|
| 1 | Create repo + structure | ✅ done | Scaffold, README, structure. |
| 2 | Bring in Forge code | ✅ done | Browser-BC committed to `forge/`, loopy to `loopy/` (135 + 53 files). Blocker resolved — this session has access to all three repos. |
| 3 | Basic integration / setup scripts | ✅ done | `vendor.sh` (now a refresh tool), `setup-forge.sh`, `setup-loopy.sh`, `bootstrap.sh` — rewritten for the **real** Forge (pure-Python server/harness, pnpm extension). |
| 4 | Test recording + distillation | ⏳ partial | **Verified runnable in-container**: deps install, server boots on :8099 + serves the panel, `/api/buckets` works, and a synthesized login `trace.json` loads + **atomizes into 1 segment** (deterministic, no LLM). classify+distill are blocked here only by **LLM access** (NVIDIA host blocked by egress policy; an Anthropic key was reachable but out of credits). One funded+reachable key away from a live `SKILL.md`. |
| 5 | Quality check + improve prompts | ⏳ pending | `SKILL.md` **contract pinned** in [architecture.md](architecture.md) from `forge/harness/distiller.py`; worked input at [`examples/login-flow/`](../examples/login-flow/). Live quality pass needs the Step 4 distilled output. |
| 6 | Documentation | ✅ done | `forge-setup.md`, `loopy-setup.md`, `architecture.md`, this file — all corrected to reality. |
| 7 | Debrief + lock loop | ⏳ pending | Run end-to-end twice with different workflows. |

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

### Remaining to lock the loop

1. Set `SF_LLM_KEY` in `forge/.env.local`.
2. `cd forge && ./scripts/start.sh`, load `forge/extension/dist/chrome-mv3`.
3. Record two short workflows → confirm each yields a `SKILL.md` that passes the
   [forge-setup.md](forge-setup.md) checklist.
4. Tune `forge/harness/distiller.py` if quality is low; re-distill.

---

## Small loops we'll run inside the big one

- "Improve the distillation prompt until the generated `SKILL.md` passes the
  quality checklist in [forge-setup.md](forge-setup.md)."
- "Make `bootstrap.sh` run clean on a fresh machine with no errors."
