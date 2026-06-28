# integration/core — orchestration

Turns a distilled `SKILL.md` into a governed, runnable Loopy-style loop and drives
a bounded run that emits a receipt. **Implemented** (Python, stdlib-only) as of
Inner Loop 2.

## Modules

| File | What it does |
|---|---|
| `skill_to_loop.py` | Parse a Forge `SKILL.md` (+ sibling `meta.json`) into a normalized `Skill`, then render a `loop.md` mapped onto Loopy's feedback cycle. Deterministic — no LLM. |
| `loop_runner.py` | Execute a `loop.md` in bounded passes with an **approval gate**, ending at a named Loopy terminal state. Delegates real browser actions to a pluggable `executor`. |
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
```

Or via the single CLI: `python -m integration.cli.forgeloop {bind,run,audit}`.

## Terminal states (never report an error as success)

`Success` · `Clean no-op` · `Blocked` · `Approval required` · `Exhausted` ·
`No progress`. A real login/form-fill loop with no human approval and no browser
executor correctly stops at **Approval required** — that's the governance seam,
not a failure.

## Not yet (next loops)

- A real browser `executor` (e.g. Playwright MCP) so an approved run acts for real.
- A catalog/registry of bound loops and a watcher over `FORGE_SKILLS_DIR`.
