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
| 7 | Debrief + lock loop | ✅ done | **2 of 2** distinct workflows distilled cleanly: `login-flow` (`login-with-credentials`) and `form-fill` (`fill-and-submit-form`). Both pass the checklist; classifier distinguishes the capabilities. Loop locked — see debrief below. |

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

### Loop locked — Step 7 debrief

Two end-to-end runs on different workflows, both clean:

| Run | Workflow | Capability | Model | Tokens (in/out) | Result |
|---|---|---|---|---|---|
| 1 | `examples/login-flow` | `login-with-credentials` | `claude-haiku-4-5` | 635 / 5329 | ✅ passes checklist; no leak |
| 2 | `examples/form-fill` | `fill-and-submit-form` | `claude-haiku-4-5` | 697 / 6983 | ✅ passes checklist; see note |

**Inner Loop 1 success criteria are all met.** Forge records (or accepts a
human-track), the harness distills, and the output is a clean, site-agnostic,
Loopy-ready `SKILL.md`.

**Findings carried forward:**

1. **Redaction happens at the recorder, not the harness.** Run #2's skill echoed
   two synthetic values (`Jane Doe`, `jane@example.com`) into an *example
   scenario* because the hand-authored trace skipped the extension's redactor
   (`forge/extension/src/redaction/`). Not a secret (fake data + reserved domain),
   but the rule is: **hand-authored traces must not contain real PII**; the live
   recording path strips it at capture.
2. **Haiku is good enough for first-pass skills** at ~6k tokens/skill (well under a
   cent). A small loop worth running later: re-distill with Opus and diff, to
   decide the default `SF_DISTILL_MODEL` before scaling.
3. **Reachability, not code, was the only blocker.** The web environment's egress
   policy blocks non-allowlisted LLM hosts (NVIDIA); use an allowlisted, funded
   endpoint (Anthropic) or run distillation outside the sandbox.

---

## Inner Loop 2 — Skill → governed Loopy loop (the integration layer)

**Goal:** turn a distilled `SKILL.md` into a governed, runnable Loopy-style loop
that executes in a bounded way and produces a receipt.

### Success criteria

- [x] A `SKILL.md` can be parsed and converted into a basic `loop.md`.
- [x] The loop includes objective, success criteria, feedback steps, and stopping
  conditions.
- [x] The loop can be executed in a bounded way and produces a receipt.
- [x] At least one example (form-fill) has a working `loop.md` + execution flow.
- [x] Basic governance/traceability is present (audit trail + approval gate).
- [x] The integration lives in `/integration/` as planned.

### What landed

| Piece | Where |
|---|---|
| `SKILL.md → Skill → loop.md` (deterministic, no LLM) | `integration/core/skill_to_loop.py` |
| Bounded runner with approval gate + terminal states | `integration/core/loop_runner.py` |
| Loopy-format run receipt | `integration/core/receipt.py` |
| Append-only audit trail (`AuditEvent`) + approval gate | `integration/governance/audit.py` |
| `forgeloop {bind,run,audit}` CLI | `integration/cli/forgeloop.py` |
| Worked examples (loop.md + RECEIPT.md) | `examples/form-fill/`, `examples/login-flow/` |

### Grounding

The `loop.md` and receipt formats are mapped onto **Loopy's real conventions**
(`loopy/skills/loopy/SKILL.md`, `references/run.md`): the Observe→Choose→Act→Verify
→Record→Repeat cycle, the six named terminal states (Success · Clean no-op ·
Blocked · Approval required · Exhausted · No progress), a finite run boundary that
is *not* invented, and the exact run-receipt shape. Section mapping is documented
in [architecture.md](architecture.md) / `integration/core/README.md`.

### Debrief

- _What worked:_ the SKILL.md contract pinned in Inner Loop 1 made a **deterministic,
  LLM-free** transform possible — every loop section comes from a real skill
  section. The approval gate makes the honest default outcome of running a
  login/form-fill loop **`Approval required`**, not a fake success.
- _Honest boundary:_ there is **no live browser executor yet**, so a real run stops
  at the gate; `--simulate` walks the full cycle but is clearly labelled and
  returns `Clean no-op`, never `Success`. Wiring a real executor (Playwright MCP)
  is Inner Loop 3.
- _Design choice:_ runtime state (audit log, persisted receipts) lives under
  `./.data/` (gitignored); the *example* `loop.md`/`RECEIPT.md` are committed as
  reference artifacts.

### Next (Inner Loop 3)

A real browser **executor** (Playwright MCP) behind the approval gate so an
approved run acts for real and reaches `Success`/`No progress` on live evidence,
plus a small **catalog** of bound loops.

---

## Small loops we'll run inside the big one

- "Improve the distillation prompt until the generated `SKILL.md` passes the
  quality checklist in [forge-setup.md](forge-setup.md)."
- "Make `bootstrap.sh` run clean on a fresh machine with no errors."
