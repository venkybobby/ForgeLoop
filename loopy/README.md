# loopy/ — vendored from loopy

This directory holds **Loopy**, the loop library + agent skill, vendored from:

> https://github.com/venkybobby/loopy

**The code here is not committed to ForgeLoop.** Everything except this `README.md`
is gitignored and pulled on demand by `scripts/vendor.sh`.

## Populate this directory

```bash
# From the repo root:
./scripts/vendor.sh            # clones/updates both forge/ and loopy/
# or just Loopy:
./scripts/vendor.sh loopy
```

If your environment's access is scoped to a single repo and `vendor.sh` is
blocked, clone it from a machine that has access and copy it in:

```bash
git clone https://github.com/venkybobby/loopy.git loopy-src
rsync -a --exclude .git loopy-src/ loopy/
```

## Expected structure (kept inside loopy/)

```
loopy/
├── loop-library/   # Loop catalog + logic (run internally/privately)
├── skill/          # Loopy skill consumed by agents
└── docs/
```

> ForgeLoop treats the loop library as internal. See
> [docs/loopy-setup.md](../docs/loopy-setup.md) for how a distilled `SKILL.md`
> becomes a runnable loop.
