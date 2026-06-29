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
| [`core/`](core/) | `SKILL.md` → `loop.md` → run → receipt; **catalog**; replay (`browser_executor`) + **agentic** (`llm_executor`) execution | ✅ implemented |
| [`governance/`](governance/) | Append-only audit trail, approval gate, pending-run/approval store (`runs.py`) | ✅ implemented |
| [`server/`](server/) | **Web control plane** — browser UI + JSON API (catalog, run, approve, receipts) | ✅ implemented |
| [`cli/`](cli/) | `forgeloop {bind,run,status,audit,catalog,dashboard,serve}` | ✅ implemented |
| [`dashboard/`](dashboard/) | Static HTML view of the catalog + runs | ✅ implemented (static generator) |

## Quick start

```bash
python -m integration.cli.forgeloop bind examples/form-fill/SKILL.md --out examples/form-fill/loop.md
python -m integration.cli.forgeloop run  examples/form-fill/loop.md --skill examples/form-fill/SKILL.md
python -m integration.cli.forgeloop status        # run results from the audit trail
python -m integration.cli.forgeloop audit         # full governance trail
python -m integration.cli.forgeloop catalog       # bound loops + latest run status
python -m integration.cli.forgeloop dashboard     # -> integration/dashboard/index.html

# Real browser execution — mandatory approval, replays the recording:
python -m pip install -r integration/requirements.txt
python scripts/live_demo.py form-fill              # -> Result: Success (+ screenshot)
python scripts/live_demo.py login-flow             # -> Result: Success
python scripts/agentic_demo.py form-fill           # LLM-driven (or scripted offline)

# Or run the whole thing as a web app and use it from a browser:
python -m integration.cli.forgeloop serve          # http://127.0.0.1:8055/
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
