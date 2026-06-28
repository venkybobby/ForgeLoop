# forge/ — vendored from Browser-BC

This directory holds **Forge**, the recording + distillation engine, vendored from:

> https://github.com/venkybobby/Browser-BC

**The code here is not committed to ForgeLoop.** Everything except this `README.md`
is gitignored and pulled on demand by `scripts/vendor.sh`. This keeps Forge easy to
update from upstream without entangling its history with ForgeLoop's.

## Populate this directory

```bash
# From the repo root:
./scripts/vendor.sh            # clones/updates both forge/ and loopy/
# or just Forge:
./scripts/vendor.sh forge
```

If you are working in an environment whose access is scoped to a single repo
(e.g. the ForgeLoop web environment), `vendor.sh` may be blocked from cloning
Browser-BC. In that case, clone it manually from a machine that has access:

```bash
git clone https://github.com/venkybobby/Browser-BC.git forge-src
# copy the relevant subfolders in:
rsync -a --exclude .git forge-src/ forge/
```

## Expected structure (kept inside forge/)

```
forge/
├── extension/   # Chrome extension — records the browser workflow
├── server/      # Ingestion server — receives recordings
├── harness/     # Distillation pipeline: atomize → classify → bucket → distill → SKILL.md
├── app/         # Control panel
└── docs/
```

> The subfolder names above mirror the plan. Adjust `scripts/vendor.sh` and
> `scripts/setup-forge.sh` if upstream uses different paths — see
> [docs/forge-setup.md](../docs/forge-setup.md).
