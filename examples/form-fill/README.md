# Example: form-fill

The **second** Inner Loop 1 workflow — distinct from `login-flow` — demonstrating
that record → distill produces a *different* capability cleanly.

## What's here

| File | Status | What |
|---|---|---|
| `trace.json` | ✅ committed | A **human-track** recording of filling a multi-field order form on `httpbin.org/forms/post` (name, phone, email, size radio, topping checkbox, comments → submit → `/post`). Values are synthetic demo data. |
| `SKILL.md` | ✅ committed | The distilled skill — real run (`claude-haiku-4-5`, distill v1). Classified as `fill-and-submit-form`. |
| `TRACE_GUIDE.md` | ✅ committed | State-machine navigation guide. |
| `loop.md` | ⏳ once produced | The Loopy loop the skill binds to. |

The trace atomizes into 1 clean segment (`/forms/post → /post`). The distiller
classified it as a **new** capability (`fill-and-submit-form`) — separate from
`login-flow`'s `login-with-credentials` — confirming the classifier distinguishes
workflow types.

## Quality note (honest finding)

The skill's **procedure is fully generalized** (no recorded values in the actual
steps), but in its invented *"Example Scenarios"* section the model echoed two
synthetic recorded values (`"Jane Doe"`, `jane@example.com`). This is **not a
secret leak** — the data is fake and `example.com` is the reserved example
domain — but it shows the abstraction isn't 100% on illustrative examples.

Why it happened: this trace was **hand-authored**, so it skipped Forge's
**recorder-side redactor** (`forge/extension/src/redaction/`), which strips PII at
capture *before* it reaches the harness in the real product. **Takeaway: never put
real PII in a hand-authored trace** — the live recording path redacts it for you.

## Reproduce

```bash
cd forge
set -a; . ./.env.local; set +a
python -m harness.main full --track-file ../examples/form-fill/trace.json
cat data/harness/skills/httpbin.org/fill-and-submit-form/SKILL.md
```
