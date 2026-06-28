# Forge setup — record a workflow, get a SKILL.md

This walks through the **Inner Loop 1** happy path: record a short browser
workflow and distill it into a clean `SKILL.md`. Forge is committed in-tree at
`forge/` (upstream: [Browser-BC](https://github.com/venkybobby/Browser-BC), aka
"Journey Forge Local"). It is **pure Python at runtime** — the server and the
distillation harness need no Node; Node/pnpm is only used to *build* the recorder
extension.

## 1. Install

```bash
./scripts/setup-forge.sh
# then set your key:
#   forge/.env.local  →  SF_LLM_KEY=sk-ant-...
```

`setup-forge.sh` copies `forge/config.example.env` → `forge/.env.local`, installs
`forge/requirements.txt` (fastapi, uvicorn, tomli), and builds the extension if
pnpm is present.

## 2. Start the ingestion server

```bash
cd forge
./scripts/start.sh            # headless dev launcher (reads .env.local)
# or, for the native window:  python entry/main.py
```

The control panel is at <http://127.0.0.1:8099/>. The server seeds the default
key (`jfl-local-dev-key`) the extension ships with, so the extension connects
automatically.

## 3. Build & load the recorder extension

```bash
cd forge/extension && pnpm install && pnpm build
```

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. **Load unpacked** → select `forge/extension/dist/chrome-mv3`.

It is pre-pointed at the local server (`127.0.0.1:8099`).

## 4. Record a workflow

Pick something small and real — logging into a site, or filling and submitting a
form. Start the recorder, perform the task, stop, label, and upload. The recording
is sent to the server (`/v1/traces/init → chunks → finalize`) and assembled into
`forge/data/traces/<id>/trace.json`.

## 5. Distill into SKILL.md

With `JFL_AUTODISTILL=1` (default in `config.example.env`) a skill appears
automatically ~1–3 min after finalize. To run it manually:

```bash
cd forge
python -m harness.main status               # see buckets + registry
python -m harness.main distill              # atomize → classify → bucket → distill
```

The harness writes, per domain + capability:

```
forge/data/harness/skills/<domain>/<capability>/
├── SKILL.md          # the distilled, reusable skill (the contract)
├── TRACE_GUIDE.md
├── meta.json
└── evidence.jsonl
```

For Claude Code, skills also auto-install under your `JFL_SKILLS_ROOT`
(`~/.claude/skills/<domain>-<capability>/SKILL.md` by default).

## 6. Quality check (the loop)

Open the generated `SKILL.md` and check:

- [ ] The **goal / capability** is stated clearly at the top.
- [ ] Steps are **atomic** and in order.
- [ ] Selectors / inputs are concrete enough to replay.
- [ ] Secrets are **not** hard-coded (referenced, not embedded — Forge redacts).
- [ ] A Loopy agent could follow it without guessing.

If quality is low, this is where loop engineering kicks in: tune the distillation
prompts in `forge/harness/distiller.py` (and `SF_MIN_BUCKET_SIZE` to require more
examples per skill), re-distill, re-check. Record what changed in
[loop-engineering.md](loop-engineering.md).

## 7. Hand off to Loopy

Once the `SKILL.md` passes, continue to [loopy-setup.md](loopy-setup.md) to bind
it to a loop and run it.

> **Skills don't grant tools.** A `SKILL.md` is injected instructions; to actually
> click/type/navigate you configure a browser MCP (Playwright) separately. See
> `forge/README.md` and `forge/docs/`.
