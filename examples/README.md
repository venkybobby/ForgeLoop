# examples/

Example workflows and the loops they become. Each example is a small,
self-contained demonstration of the full ForgeLoop path:

```
record  →  SKILL.md  →  bound loop  →  governed run
```

## Examples

- **[login-flow/](login-flow/)** — ✅ a recorded login workflow
  (`the-internet.herokuapp.com`). The `trace.json` is committed and validated
  (loads + atomizes into 1 segment); run the harness to distill its `SKILL.md`.
- **form-fill/** — ⏳ planned: record filling and submitting a form; the loop
  retries until the submission is confirmed.

Each example contains:

```
<example>/
├── README.md       # what it does and how to run it
├── trace.json      # the recorded workflow (human-track input)
├── SKILL.md        # the distilled skill (committed once produced)
└── loop.md         # the Loopy loop definition it binds to
```

> The Forge code is committed in-tree (`forge/`), so examples no longer depend on
> a vendoring step — only on an LLM key for the distill stage. Examples graduate to
> a full record→distill→loop run during **Inner Loop 1, Step 7**. See
> [../docs/loop-engineering.md](../docs/loop-engineering.md).
