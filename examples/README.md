# examples/

Example workflows and the loops they become. Each example is a small,
self-contained demonstration of the full ForgeLoop path:

```
record  →  SKILL.md  →  bound loop  →  governed run
```

## Planned examples

- **login-flow/** — record logging into a demo site; the skill becomes a loop that
  verifies it can reach an authenticated page.
- **form-fill/** — record filling and submitting a form; the loop retries until the
  submission is confirmed.

Each example will contain:

```
<example>/
├── README.md       # what it does and how to run it
├── SKILL.md        # the distilled skill (committed once produced)
└── loop.md         # the Loopy loop definition it binds to
```

> Examples are added during **Inner Loop 1, Step 7** (run end-to-end twice with
> different workflows). They depend on the upstream Forge code being vendored —
> see [../docs/loop-engineering.md](../docs/loop-engineering.md).
