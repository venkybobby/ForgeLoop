# integration/ — the ForgeLoop glue layer

This is where **most new ForgeLoop development happens.** Forge and Loopy stay
close to their upstreams (vendored in `forge/` and `loopy/`); the integration
layer is the product we build on top of them.

**Stack: Python** (stdlib-only). Locked once the real interfaces were in hand:
Forge's harness is pure Python and emits `SKILL.md` + `meta.json`, and Loopy is a
set of Markdown skills/conventions — so the glue is a small, dependency-free Python
layer that reads those files and drives bounded runs.

## The four modules

| Module | Responsibility | Status |
|--------|----------------|--------|
| [`core/`](core/) | Orchestration: `SKILL.md` → `loop.md` → bounded run → receipt | ✅ implemented (Inner Loop 2) |
| [`governance/`](governance/) | Append-only audit trail + approval gate | ✅ implemented (audit + gate) |
| [`cli/`](cli/) | `forgeloop {bind,run,audit}` over core + governance | ✅ implemented |
| [`dashboard/`](dashboard/) | Web UI to browse skills, loops, and runs | ⏳ design only |

## Quick start

```bash
python -m integration.cli.forgeloop bind examples/form-fill/SKILL.md --out examples/form-fill/loop.md
python -m integration.cli.forgeloop run  examples/form-fill/loop.md --skill examples/form-fill/SKILL.md
python -m integration.cli.forgeloop status        # run results from the audit trail
python -m integration.cli.forgeloop audit         # full governance trail

# Real browser execution (Inner Loop 3) — mandatory approval, replays the recording:
python -m pip install -r integration/requirements.txt
python scripts/live_demo.py                        # form-fill -> Result: Success (+ screenshot)
```

## Data flow

```
forge/harness  ──SKILL.md──►  core (register)  ──►  catalog
                                   │
                          governance (approve?)
                                   │
                                   ▼
                          loopy (run loop)  ──events──►  governance (trace/audit)
                                   │
                                   ▼
                              dashboard (observe)
```

`core`, `governance`, and `cli` are **implemented** — see each module's README and
the worked examples in [`../examples/`](../examples/). `dashboard` is still a design
README. A skill **catalog/registry** and a real browser **executor** are the next
pieces (Inner Loop 3+).
