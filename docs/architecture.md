# ForgeLoop architecture

## The one-sentence model

**Forge produces skills; Loopy runs them in loops; the integration layer governs
the handoff.**

## Subsystems

### Forge (`forge/`, vendored from Browser-BC)
The recording + distillation engine.

- **extension** — a Chrome extension that records a browser workflow (clicks,
  navigations, inputs) as the user performs it.
- **server** — an ingestion server that receives recordings from the extension.
- **harness** — the distillation pipeline that turns a raw recording into a clean
  `SKILL.md`: **atomize → classify → bucket → distill**.
- **app** — a control panel for managing recordings and distillation.

The harness's output, `SKILL.md`, is the contract between Forge and the rest of
ForgeLoop.

### Loopy (`loopy/`, vendored from loopy)
The loop runtime.

- **loop-library** — the catalog of loops and their logic (treated as internal).
- **skill** — the Loopy skill that agents invoke to run a loop: define a clear
  goal, then iterate until it's met.

### Integration (`integration/`, new code)
The glue. See [integration/README.md](../integration/README.md). Modules: `core`
(orchestration), `dashboard` (UI), `governance` (audit/traces/approvals), `cli`.

## Why `forge/` and `loopy/` are vendored, not submodules or committed copies

We considered three options:

1. **Commit copies** of the upstream code directly into ForgeLoop. Rejected:
   entangles histories and makes upstream updates painful.
2. **Git submodules.** Workable, but submodules are awkward in restricted
   environments (the gitlink needs network access to resolve, and CI/web
   sessions scoped to a single repo can't fetch them).
3. **Vendor on demand** (chosen). `forge/` and `loopy/` are gitignored except for
   a `README.md` placeholder; `scripts/vendor.sh` clones the upstream forks into
   them locally. Upstream history stays upstream; ForgeLoop tracks only its own
   code plus instructions for reconstituting the vendored dirs.

If we later want pinned versions, `vendor.sh` already accepts `FORGE_REF` /
`LOOPY_REF` environment variables to lock a branch or SHA.

## The SKILL.md contract (to be finalized)

`core` parses `SKILL.md` into a normalized `Skill` (id, title, goal, steps,
metadata). The exact front-matter schema is **TBD** — it gets pinned down by
reading the harness output during Inner Loop 1, Step 5, then documented here.

## Known constraints

- **Restricted-access environments.** When a session's repo access is scoped to
  `forgeloop` only (as in the ForgeLoop web environment), `vendor.sh` cannot clone
  Browser-BC / loopy and the upstream code must be brought in from a machine with
  access. This is why the scaffold is fully functional without the upstream code
  present.
