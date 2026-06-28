# Example: login-flow

A minimal, self-contained demonstration of the **record → distill → SKILL.md**
half of the ForgeLoop path, using a recorded login workflow.

## What's here

| File | Status | What |
|---|---|---|
| `trace.json` | ✅ committed | A **human-track** recording of logging into `the-internet.herokuapp.com` (username → password → submit → reaches `/secure`). Uses the site's **public demo credentials** (`tomsmith` / `SuperSecretPassword!`) — never put real secrets in a committed trace. |
| `SKILL.md` | ✅ committed | The distilled skill — produced by a real run (`claude-haiku-4-5`, distill v1). Passes the quality checklist; site-agnostic; no credentials leaked. |
| `TRACE_GUIDE.md` | ✅ committed | The state-machine navigation guide emitted alongside the skill. |
| `meta.json` / `evidence.jsonl` | ✅ committed | Distill provenance + source-segment evidence. |
| `loop.md` / `RECEIPT.md` | ✅ committed | The governed Loopy loop and a run receipt (`Approval required`), from `integration/` (Inner Loop 2). Bind/run: `python -m integration.cli.forgeloop bind examples/login-flow/SKILL.md --out examples/login-flow/loop.md`. |

`trace.json` is validated: it loads via the harness adapter (auto-detected as
`human-tracks`) and **atomizes into 1 clean segment** (`/login → /secure`,
boundary `path_change`) with no LLM required. The remaining stages (classify,
distill) call the configured LLM.

## Produce the SKILL.md

From the repo root, with Forge installed (`./scripts/setup-forge.sh`) and an LLM
key set in `forge/.env.local` (`SF_LLM_KEY`, plus `SF_LLM_BASE` /
`SF_DISTILL_MODEL` / `SF_CLASSIFY_MODEL` for a non-Anthropic gateway):

```bash
cd forge
set -a; . ./.env.local; set +a
python -m harness.main full --track-file ../examples/login-flow/trace.json
python -m harness.main status      # 1 segment, 1 bucket, 1 distilled skill
cat data/harness/skills/the-internet.herokuapp.com/*/SKILL.md
```

Copy the resulting `SKILL.md` back into this folder once it passes the quality
checklist in [../../docs/forge-setup.md](../../docs/forge-setup.md).

## The human-track schema (for hand-authoring more traces)

```jsonc
{
  "schema_version": "human_tracks_v1",
  "case_id": "unique-id",
  "domain": "example.com",
  "task_instruction": "what the user was trying to do",
  "navigation_chain": ["example.com"],
  "events": [
    { "type": "pageLoad", "url": "https://example.com/login", "ts": 0 },
    { "type": "click",  "url": "...", "ts": 1200,
      "target": { "tagName": "INPUT", "id": "username", "xpath": "//*[@id=\"username\"]" } },
    { "type": "input",  "url": "...", "ts": 2100,
      "target": { "tagName": "INPUT", "id": "username" }, "value": "user" }
  ],
  "outcome": { "success": true, "final_url": "https://example.com/secure" }
}
```

> The distiller is prompted to **generalize away site-specific selectors**, so the
> produced skill should apply to any login form — not just this demo site.
