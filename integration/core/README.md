# integration/core — orchestration

Turns a distilled `SKILL.md` into a registered, runnable, governed loop, and
drives a run to completion.

## Responsibilities

1. **Ingest skills.** Watch `FORGE_SKILLS_DIR` for new/updated `SKILL.md` files
   produced by `forge/harness`. Parse front-matter + steps into a normalized
   `Skill` record.
2. **Register into the catalog.** Maintain the canonical list of available
   skills and the loops derived from them.
3. **Bind skill → loop.** Map a skill's steps onto a Loopy loop definition
   (`loopy/loop-library`) so the agent has a clear goal + iteration structure.
4. **Drive runs.** Start a loop run, stream events to `governance/`, honor
   approval gates, and record the final outcome.

## Proposed contract (stack-agnostic)

```
Skill {
  id          string          # stable slug
  title       string
  source      string          # path to the originating SKILL.md
  goal        string          # the loop's success condition
  steps       Step[]          # ordered, atomized actions
  metadata    map<string,any> # tags, target site, auth requirements, ...
}

registerSkill(path) -> Skill           # parse + add to catalog
listSkills() -> Skill[]
bindLoop(skillId) -> LoopDef           # skill -> Loopy loop definition
startRun(skillId, input) -> RunHandle  # begin a governed run
```

## Open questions (resolve once upstream is vendored)

- Exact `SKILL.md` schema emitted by `forge/harness` (front-matter keys, step format).
- Loopy loop definition format and entry point in `loopy/loop-library`.
- Whether core hosts a long-running service or runs as a CLI-invoked library.

> Status: **design only.** No executable code yet — see
> [../../docs/loop-engineering.md](../../docs/loop-engineering.md).
