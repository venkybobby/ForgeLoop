"""receipt — the evidence-backed run receipt for a ForgeLoop loop run.

Mirrors the Loopy run-receipt format from
`loopy/skills/loopy/references/run.md` so receipts are interchangeable with
Loopy's own. Pure data + rendering; no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# The six named terminal states Loopy defines. An error or exhausted budget is
# NEVER reported as success.
TERMINAL_STATES = (
    "Success",
    "Clean no-op",
    "Blocked",
    "Approval required",
    "Exhausted",
    "No progress",
)


@dataclass
class Receipt:
    loop: str                       # title or identifier
    definition: str                 # exact loop text ref, or SHA-256 + key fields
    scope: str                      # what was inspected or changed
    check: str                      # acceptance check + recorded conditions
    boundary: str                   # finite run limit
    result: str                     # one of TERMINAL_STATES
    evidence: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    next: str = "nothing"           # remaining work / exact approval or blocker
    ts: str | None = None           # ISO-8601, supplied by caller (not generated)

    def __post_init__(self) -> None:
        if self.result not in TERMINAL_STATES:
            raise ValueError(
                f"result {self.result!r} is not a terminal state {TERMINAL_STATES}"
            )

    def render(self) -> str:
        def block(items: list[str]) -> str:
            return "\n".join(f"- {i}" for i in items) if items else "- (none)"

        stamp = f"\nTimestamp: {self.ts}" if self.ts else ""
        return f"""\
## Loopy run receipt

Loop: {self.loop}
Definition: {self.definition}
Scope: {self.scope}
Check: {self.check}
Boundary: {self.boundary}
Result: {self.result}{stamp}

Evidence:
{block(self.evidence)}

Actions:
{block(self.actions)}

Next: {self.next}
"""

    def to_dict(self) -> dict:
        return {
            "loop": self.loop,
            "definition": self.definition,
            "scope": self.scope,
            "check": self.check,
            "boundary": self.boundary,
            "result": self.result,
            "evidence": self.evidence,
            "actions": self.actions,
            "next": self.next,
            "ts": self.ts,
        }
