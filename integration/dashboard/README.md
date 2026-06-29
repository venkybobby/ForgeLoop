# integration/dashboard — UI

A **static** dashboard over the loop catalog + governance audit trail. `build.py`
bakes the data into a single self-contained `index.html` (no server, no runtime
dependency) — open it straight from disk.

## Generate

```bash
python -m integration.dashboard.build            # -> integration/dashboard/index.html
# or via the CLI:
python -m integration.cli.forgeloop dashboard
```

It renders:

- **Catalog** — every skill/loop (id, domain, distill model, whether a `loop.md`
  and receipt exist) with its latest run result as a coloured badge.
- **Recent runs** — the last runs from the audit trail with their terminal state.

A committed snapshot (`index.html`) is included as an example; regenerate it any
time. Runtime audit data lives under `./.data/` (gitignored), so the dashboard is
a read-only view you rebuild on demand.

> Status: **implemented (static generator).** A live server with an approve
> button (the `POST /runs/:id/approve` surface below) is future work; today
> approval is granted at run time via `forgeloop run --approve`.

## Future interactive surface

```
GET  /skills · /loops · /runs · /runs/:id
POST /runs/:id/approve   satisfy a governance approval gate
```
