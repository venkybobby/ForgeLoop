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

- [ ] ForgeLoop repo exists with the agreed structure.
- [ ] Forge's extension + server + harness are integrated and runnable.
- [ ] A user can record a workflow and get a clean `SKILL.md`.
- [ ] The skill is good enough to be consumed by Loopy.
- [ ] Basic setup instructions exist.

### Step status

| # | Step | State | Notes |
|---|------|-------|-------|
| 1 | Create repo + structure | ✅ done | Scaffold, README, structure committed. |
| 2 | Bring in Forge code | ⛔ blocked | `vendor.sh` ready, but Browser-BC is **403** in this access-scoped environment. Needs repo access or manual copy. |
| 3 | Basic integration / setup scripts | ✅ done | `vendor.sh`, `setup-forge.sh`, `setup-loopy.sh`, `bootstrap.sh`. |
| 4 | Test recording + distillation | ⏳ pending | Requires Step 2. |
| 5 | Quality check + improve prompts | ⏳ pending | Requires Step 4. |
| 6 | Documentation | ✅ done | `forge-setup.md`, `loopy-setup.md`, `architecture.md`, this file. |
| 7 | Debrief + lock loop | ⏳ pending | Run end-to-end twice with different workflows. |

### Current blocker

This development environment's GitHub access is **scoped to `venkybobby/forgeloop`
only**. Cloning `venkybobby/Browser-BC` and `venkybobby/loopy` returns HTTP 403 at
the proxy — forking did not change this, because the scope is enforced on the
session token, not on repo ownership.

**To unblock Step 2, do one of:**
- Add `Browser-BC` and `loopy` to the web environment's allowed-repo scope, then
  re-run this session; or
- Run `./scripts/vendor.sh` from a machine/environment that can reach those repos;
  or
- Push the Forge/Loopy code into `forgeloop` directly so it's in scope.

Everything that does **not** depend on the upstream code (structure, scripts,
glue-layer design, docs) is complete and committed.

### What worked / what was hard (fill in as we go)

- _What worked:_ scaffold + scripts + docs landed cleanly without the upstream code.
- _What was hard:_ access scoping blocks vendoring the two source repos in this
  environment.

---

## Small loops we'll run inside the big one

- "Improve the distillation prompt until the generated `SKILL.md` passes the
  quality checklist in [forge-setup.md](forge-setup.md)."
- "Make `bootstrap.sh` run clean on a fresh machine with no errors."
