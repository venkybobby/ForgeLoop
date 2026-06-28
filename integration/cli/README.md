# integration/cli — command-line tools

Thin command-line entry points over `core` and `governance`, for users who'd
rather not open the dashboard.

## Intended commands

```
forgeloop skills list                 # list ingested skills
forgeloop skills show <id>            # print a skill's goal + steps
forgeloop skills register <path>      # ingest a SKILL.md by path
forgeloop loop bind <skill-id>        # bind a skill to a Loopy loop
forgeloop run start <skill-id>        # start a governed run
forgeloop run watch <run-id>          # stream a run's trace
forgeloop run approve <run-id>        # satisfy an approval gate
forgeloop audit tail                  # follow the audit log
```

The CLI shells into the same `core`/`governance` logic the dashboard uses — no
business logic lives here, only argument parsing and output formatting.

> Status: **design only.** Implemented once the integration stack is locked.
