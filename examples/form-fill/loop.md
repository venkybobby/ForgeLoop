## Fill and Submit Form Loop

This skill automates the completion and submission of web forms. It involves identifying form fields, populating them with appropriate data, selecting required options, and triggering submission to reach a confirmation or results page. The loop runs bounded passes and stops at a named terminal state — it
is a feedback system, not permission for unbounded autonomy.

- **Skill id:** `httpbin.org::fill-and-submit-form`
- **Source skill:** `examples/form-fill/SKILL.md`
- **Distilled by:** `claude-haiku-4-5`

## Objective

This skill automates the completion and submission of web forms. It involves identifying form fields, populating them with appropriate data, selecting required options, and triggering submission to reach a confirmation or results page.

## Trigger

Use this skill when: A form is present on the page and requires completion; You need to submit data to a server via a web form

## Success / acceptance criteria

The loop succeeds only when these are observably true (never report an error or an
exhausted budget as success):

- The submit button was clicked
- The page has navigated to a new URL (not the form URL)
- The new page displays content indicating successful form processing
- No error messages related to form validation are visible

## Feedback cycle

Each pass follows Loopy's Observe → Choose → Act → Verify → Record → Repeat/stop:

1. **Observe** — read fresh page state and the agreed evidence.
2. **Choose** — pick the next checkpoint from the worklist:
   - Form structure identified and all fields catalogued
   - Required fields populated with valid data
   - Optional selections (radio, checkbox, dropdown) completed
   - Textareas and multi-line fields completed
   - All visible validation errors resolved
   - Submit button located and clicked
   - Page navigation detected
   - Results/confirmation page loaded and content verified
3. **Act** — take one bounded, reversible action toward that checkpoint.
4. **Verify** — re-run the acceptance check; do not confuse these *false terminal
   states* with success:
   - Form filled but not submitted: Fields are populated, but submit button was not clicked
   - Submit button clicked but no page navigation: Page stays on form URL; may indicate validation errors or button malfunction
   - Modal or overlay appears: Dialog box opens instead of page navigation
   - Form reloads with validation errors: Page returns to the form with red error messages
   - Submit button is loading: Spinner visible but page has not navigated yet
   - Page shows loading state indefinitely: Spinner continues for >10 seconds without navigation
5. **Record** — save the action, evidence, outcome, and remaining work.
6. **Repeat or stop** — continue only while progress is measurable and the boundary
   holds. On failure, apply a recovery policy and learn:
   - Recovery A: Missing or Incomplete Field Data
   - Recovery B: Invalid Field Format
   - Recovery C: Submit Button Not Responding
   - Recovery D: Form Reloads Instead of Submitting
   - Recovery E: Page Becomes Unresponsive
   - Recovery F: Redirect Loop

## Stopping conditions

- **Terminal states:** Success · Clean no-op · Blocked · Approval required ·
  Exhausted · No progress.
- **Run boundary:** operator-supplied limit of 8 passes.
- **No-progress stop:** halt when a pass produces no measurable change toward the
  acceptance criteria.

## Governance

- **Approval gate:** side-effecting browser actions (logins, submissions,
  purchases, external messages) require explicit human approval before they run.
  Without approval the loop halts at **Approval required**.
- **Red lines (never violate):**
- NEVER submit a form with intentionally malicious data (SQL injection, XSS payloads, etc.) unless explicitly instructed
- NEVER click the submit button multiple times in rapid succession
- NEVER skip validation errors
- NEVER leave required fields empty and attempt to submit
- NEVER assume submission is complete until a new page loads
- NEVER interact with unrelated page elements while submission is in progress
- NEVER ignore the form's visual validation (red borders, error text, asterisks)
- **Security boundaries:**
- Only act on HTTPS pages whose domain matches the intended target.
- **Traceability:** every run emits an audit event and a run receipt
  (see `integration/governance/` and `integration/core/receipt.py`).

Prompt:
> This skill automates the completion and submission of web forms. It involves identifying form fields, populating them with appropriate data, selecting required options, and triggering submission to reach a confirmation or results page. Work in bounded passes: observe the page, take the single next in-scope action, then verify against the acceptance check. Keep only verified progress. Stop when the submit button was clicked, or on no measurable progress. Ask before never submit a form with intentionally malicious data (sql injection, xss payloads, etc.) unless explicitly instructed or any side-effecting browser action.

---
_Generated from `examples/form-fill/SKILL.md` (SHA-256 `a636bdff08c00815…`) by
`integration/core/skill_to_loop.py`. This is a ForgeLoop adaptation of the Forge
skill into a Loopy-style loop — not a published Loop Library loop._
