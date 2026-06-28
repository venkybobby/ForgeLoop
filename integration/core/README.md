# integration/core — orchestration

Turns a distilled `SKILL.md` into a governed, runnable Loopy-style loop and drives
a bounded run that emits a receipt. **Implemented** (Python, stdlib-only) as of
Inner Loop 2.

## Modules

| File | What it does |
|---|---|
| `skill_to_loop.py` | Parse a Forge `SKILL.md` (+ sibling `meta.json`) into a normalized `Skill`, then render a `loop.md` mapped onto Loopy's feedback cycle. Deterministic — no LLM. |
| `loop_runner.py` | Execute a `loop.md` in bounded passes with an **approval gate**, ending at a named Loopy terminal state. `run_loop` (gate/simulate) and `run_live` (real browser). |
| `browser_executor.py` | **Real** browser actions via Playwright (navigate/click/fill/observe) over the pre-installed Chromium; `actions_from_trace()` replays a recording. |
| `receipt.py` | The evidence-backed run receipt, in Loopy's `references/run.md` format. |

## The `Skill` record (parsed from SKILL.md)

```
Skill {
  id              "<domain>::<capability>"   # e.g. httpbin.org::fill-and-submit-form
  title, source, sha256
  objective, trigger
  acceptance[]       # observable success / terminal conditions  -> the success gate
  milestones[]       # the worklist / checkpoints                -> Choose step
  false_terminals[]  # "looks done but isn't" guards             -> Verify step
  recovery[]         # what a failed pass learns                 -> Repeat/learn step
  red_lines[], security[]   # never-violate rules                -> Governance
  steps[]            # ordered procedure phases
  metadata           # from meta.json (model, domains, ...)
}
```

## How a SKILL.md maps onto a loop

| SKILL.md section | loop.md role (Loopy) |
|---|---|
| Purpose / Overview | Objective |
| When to Use | Trigger |
| Terminal Conditions / Success Criteria | **Success / acceptance criteria** (the observable gate) |
| Milestones | the **Choose** worklist in the feedback cycle |
| False Terminal States | **Verify** guards (don't stop early) |
| Recovery / Failure Modes | **Repeat-or-stop** learning |
| Red Lines + Security Boundaries | **Governance** (approval gate + never-violate) |

## Usage

```bash
# 1. Bind a skill into a loop
python -m integration.core.skill_to_loop examples/form-fill/SKILL.md \
    --out examples/form-fill/loop.md --max-passes 8

# 2. Run it (held at the approval gate by default — side-effecting actions
#    require explicit human approval)
python -m integration.core.loop_runner examples/form-fill/loop.md \
    --skill examples/form-fill/SKILL.md --out examples/form-fill/RECEIPT.md

# 2b. Walk the full feedback cycle with a side-effect-free simulated executor
python -m integration.core.loop_runner examples/form-fill/loop.md \
    --skill examples/form-fill/SKILL.md --simulate

# 2c. REAL browser run (Inner Loop 3) — mandatory approval; replays the trace
python -m pip install -r integration/requirements.txt   # Playwright (Chromium pre-installed)
python scripts/live_demo.py                              # -> Result: Success (+ RECEIPT.live.md, screenshot)
```

Or via the single CLI: `python -m integration.cli.forgeloop {bind,run,audit,status}`.

## Terminal states (never report an error as success)

`Success` · `Clean no-op` · `Blocked` · `Approval required` · `Exhausted` ·
`No progress`. A real login/form-fill loop with no human approval and no browser
executor correctly stops at **Approval required** — that's the governance seam,
not a failure.

## Not yet (next loops)

- A skill **catalog/registry** of bound loops and a watcher over `FORGE_SKILLS_DIR`.
- A web **dashboard** to browse skills, loops, and runs.
- Live execution against **public** sites (the sandbox blocks egress, so the live
  demo serves the target locally; the mechanism is identical for a reachable site).
