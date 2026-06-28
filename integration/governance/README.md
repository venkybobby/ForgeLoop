# integration/governance — audit, traces, approval gates

Makes ForgeLoop runs **observable and controllable**. Every loop run is recorded;
side-effecting runs require human approval before they proceed. **Audit + approval
gate implemented** (`audit.py`) as of Inner Loop 2.

## Responsibilities

1. **Audit log** — _implemented_ (`audit.py`). Append-only JSONL record of every
   meaningful event (`loop.created`, `run.started`, `run.finished`,
   `approval.granted`, …) at `GOVERNANCE_AUDIT_DIR/audit.jsonl`
   (default `./.data/audit/`, gitignored). `record_event(...)` / `read_events(...)`.
2. **Run traces** — partial. `loop_runner` persists a per-run receipt
   (`receipt.py`) and records start/finish events. A richer per-step trace is future.
3. **Approval gates** — _implemented_. `loop_runner` holds at **Approval required**
   before any side-effecting browser action unless `--approve` is given; with
   approval but no executor it stops **Blocked** rather than faking success.

## Event shape (proposed)

```
AuditEvent {
  ts        string        # ISO-8601, supplied by caller (not generated here)
  actor     string        # user | agent | system
  kind      string        # skill.registered | run.started | approval.requested | ...
  subject   string        # skill id / run id
  detail    map<string,any>
}
```

## Why approval gates matter

Forge skills automate real browser actions (logins, form submissions, purchases).
Running them in an unattended loop is powerful and risky. The gate is the seam
where a human stays in control before anything irreversible happens.

## Inspect the trail

```bash
python -m integration.cli.forgeloop audit            # all events
python -m integration.cli.forgeloop audit --subject httpbin.org::fill-and-submit-form -v
```

> Status: **audit + approval gate implemented**; richer per-step run traces and a
> dashboard view are future work.
