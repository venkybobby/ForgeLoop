# integration/governance — audit, traces, approval gates

Makes ForgeLoop runs **observable and controllable**. Every loop run is recorded;
side-effecting runs can require human approval before they proceed.

## Responsibilities

1. **Audit log.** Append-only record of every meaningful event: skill registered,
   loop bound, run started/finished, approval requested/granted. Written to
   `GOVERNANCE_AUDIT_DIR`.
2. **Run traces.** Per-run, step-by-step trace (inputs, agent actions, outputs,
   errors) written to `LOOPY_RUNS_DIR`, linkable from the dashboard.
3. **Approval gates.** When `GOVERNANCE_APPROVAL_REQUIRED=true`, a run pauses at
   its first side-effecting step until a human approves via the dashboard/CLI.

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

> Status: **design only.**
