# integration/dashboard — web UI

A simple self-hosted UI over the `core` APIs. Three views:

- **Skills** — every `SKILL.md` ingested from `forge/harness`, with its goal,
  steps, and source recording.
- **Loops** — skills bound to Loopy loop definitions; their configuration and
  approval requirements.
- **Runs** — live and historical runs, their status, and a link to the full
  trace in `governance/`.

## Intended surface

```
GET  /skills            list skills
GET  /skills/:id        skill detail (goal, steps, source)
GET  /loops             list bound loops
GET  /runs              list runs (filter by status)
GET  /runs/:id          run detail + streamed events
POST /runs/:id/approve  satisfy a governance approval gate
```

Served on `DASHBOARD_PORT` (default `3000`). Reads from `core`; writes only
approvals, which flow through `governance`.

> Status: **design only.** Framework chosen when the integration stack is locked.
