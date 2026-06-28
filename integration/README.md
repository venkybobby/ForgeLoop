# integration/ — the ForgeLoop glue layer

This is where **most new ForgeLoop development happens.** Forge and Loopy stay
close to their upstreams (vendored in `forge/` and `loopy/`); the integration
layer is the product we build on top of them.

The stack for this layer is intentionally **undecided** until the upstream Forge
and Loopy code is in hand — Forge's extension+server strongly imply Node/TypeScript,
while a distillation/loop runtime is often Python. Once `vendor.sh` has run and we
can see the real interfaces, we lock the stack (tracked as a decision in
[../docs/architecture.md](../docs/architecture.md)).

## The four modules

| Module | Responsibility | Consumes | Produces |
|--------|----------------|----------|----------|
| [`core/`](core/) | Orchestration: turn a `SKILL.md` into a registered, runnable loop and drive it end-to-end | Forge skills, Loopy library | runs |
| [`dashboard/`](dashboard/) | Web UI to browse skills, loops, and runs | core APIs | UI |
| [`governance/`](governance/) | Audit logs, run traces, approval gates | run events | audit trail |
| [`cli/`](cli/) | Command-line entry points for the above | core APIs | terminal output |

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

Each module currently ships a **design README** describing its contract. Code
lands once the stack is locked — see each module's README for its intended
surface.
