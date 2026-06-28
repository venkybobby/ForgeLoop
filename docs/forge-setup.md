# Forge setup — record a workflow, get a SKILL.md

This walks through the **Inner Loop 1** happy path: record a short browser
workflow and distill it into a clean `SKILL.md`.

> Prerequisite: the upstream Forge code must be present in `forge/`. Run
> `./scripts/vendor.sh forge` first. If your environment can't clone Browser-BC,
> see [forge/README.md](../forge/README.md) for the manual copy path.

## 1. Install

```bash
cp .env.example .env          # then set ANTHROPIC_API_KEY
./scripts/setup-forge.sh
```

## 2. Start the ingestion server

```bash
# exact command depends on forge/server's package — typically one of:
( cd forge/server && npm run dev )      # or: npm start
```

The server listens on `FORGE_SERVER_PORT` (default `4000`) and writes recordings
to `FORGE_DATA_DIR`.

## 3. Load the Chrome extension

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. **Load unpacked** → select `forge/extension`.
4. Confirm the extension points at `http://localhost:4000` (or your
   `FORGE_SERVER_*` values).

## 4. Record a workflow

Pick something small and real — logging into a site, or filling and submitting a
form. Start the recorder in the extension, perform the workflow, then stop. The
recording is sent to the server.

## 5. Distill into SKILL.md

```bash
# exact command depends on forge/harness — typically:
( cd forge/harness && npm run distill )    # or a python entrypoint
```

The harness runs **atomize → classify → bucket → distill** and writes a
`SKILL.md` into `FORGE_SKILLS_DIR` (default `./.data/skills`).

## 6. Quality check (the loop)

Open the generated `SKILL.md` and check:

- [ ] The **goal** is stated clearly at the top.
- [ ] Steps are **atomic** and in order.
- [ ] Selectors / inputs are concrete enough to replay.
- [ ] Secrets are **not** hard-coded (they should be referenced, not embedded).
- [ ] A Loopy agent could follow it without guessing.

If quality is low, this is where loop engineering kicks in: improve the
distillation prompts in `forge/harness`, re-distill, re-check. Repeat until the
checklist passes. Record what changed in
[loop-engineering.md](loop-engineering.md).

## 7. Hand off to Loopy

Once the `SKILL.md` passes, continue to [loopy-setup.md](loopy-setup.md) to bind
it to a loop and run it.

> The exact `npm run` / python commands above are placeholders until the upstream
> harness is vendored and inspected — they'll be pinned to the real entrypoints
> during Inner Loop 1.
