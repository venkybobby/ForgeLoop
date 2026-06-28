# Loopy setup — run a skill as a loop

Once Forge has produced a good `SKILL.md`, Loopy runs it as a structured loop:
**define a clear goal → iterate until the goal is met.**

> Prerequisite: the upstream Loopy code must be present in `loopy/`. Run
> `./scripts/vendor.sh loopy` first.

## 1. Install

```bash
./scripts/setup-loopy.sh
```

## 2. Register the skill

The integration `core` ingests `SKILL.md` files from `FORGE_SKILLS_DIR`. Until
`core` is implemented, register manually by pointing Loopy at the skill file.

```bash
# once integration/cli exists:
forgeloop skills register ./.data/skills/<your-skill>.md
forgeloop loop bind <skill-id>
```

## 3. Run the loop (governed)

```bash
forgeloop run start <skill-id>
forgeloop run watch <run-id>
```

If `GOVERNANCE_APPROVAL_REQUIRED=true`, the run pauses before its first
side-effecting step:

```bash
forgeloop run approve <run-id>
```

## 4. Observe

Traces are written to `LOOPY_RUNS_DIR` and the audit log to
`GOVERNANCE_AUDIT_DIR`. Browse them in the dashboard (`DASHBOARD_PORT`, default
`3000`) or with `forgeloop audit tail`.

## The skill → loop mapping

A Forge `SKILL.md` provides the **goal** and the **steps**. Loopy provides the
**iteration**: it attempts the steps, checks the goal, and retries/adjusts until
the goal condition is satisfied or it gives up. The mapping is owned by
`integration/core` (`bindLoop`) — see
[../integration/core/README.md](../integration/core/README.md).

> Commands above use the planned `forgeloop` CLI; it is design-only today. The
> exact Loopy entrypoints are pinned once `loopy/` is vendored and inspected.
