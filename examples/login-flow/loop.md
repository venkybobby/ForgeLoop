## Login with Credentials Loop

Authenticate a user by submitting valid username and password credentials through a login form. The loop runs bounded passes and stops at a named terminal state — it
is a feedback system, not permission for unbounded autonomy.

- **Skill id:** `herokuapp.com::login-with-credentials`
- **Source skill:** `examples/login-flow/SKILL.md`
- **Distilled by:** `claude-haiku-4-5`

## Objective

Authenticate a user by submitting valid username and password credentials through a login form.

## Trigger

Use this skill whenever you need to access a protected resource or authenticated user session. The skill should be invoked when a login page is detected or when credentials are required to proceed.

## Success / acceptance criteria

The loop succeeds only when these are observably true (never report an error or an
exhausted budget as success):

- The page URL has changed from the login page to an authenticated resource
- The new page displays user-specific or authenticated content
- No login form is visible on the new page
- The page load completes without error
- Session/auth cookies or tokens are present in browser storage

## Feedback cycle

Each pass follows Loopy's Observe → Choose → Act → Verify → Record → Repeat/stop:

1. **Observe** — read fresh page state and the agreed evidence.
2. **Choose** — pick the next checkpoint from the worklist:
   - Username field located and focused
   - Username entered into field
   - Password field located and focused
   - Password entered into field
   - Submit button located
   - Submit button clicked
   - Page navigation initiated
   - New page loaded (URL changed)
   - Authenticated content verified
3. **Act** — take one bounded, reversible action toward that checkpoint.
4. **Verify** — re-run the acceptance check; do not confuse these *false terminal
   states* with success:
   - (none recorded)
5. **Record** — save the action, evidence, outcome, and remaining work.
6. **Repeat or stop** — continue only while progress is measurable and the boundary
   holds. On failure, apply a recovery policy and learn:
   - Login Form Still Visible
   - Invalid Credentials Error
   - Redirected Back to Login
   - CAPTCHA or MFA Required
   - Page Loads Indefinitely
   - Field Not Found

## Stopping conditions

- **Terminal states:** Success · Clean no-op · Blocked · Approval required ·
  Exhausted · No progress.
- **Run boundary:** operator-supplied limit of 6 passes.
- **No-progress stop:** halt when a pass produces no measurable change toward the
  acceptance criteria.

## Governance

- **Approval gate:** side-effecting browser actions (logins, submissions,
  purchases, external messages) require explicit human approval before they run.
  Without approval the loop halts at **Approval required**.
- **Red lines (never violate):**
- No irreversible or out-of-scope actions.
- **Security boundaries:**
- Only act on HTTPS pages whose domain matches the intended target.
- **Traceability:** every run emits an audit event and a run receipt
  (see `integration/governance/` and `integration/core/receipt.py`).

Prompt:
> Authenticate a user by submitting valid username and password credentials through a login form. Work in bounded passes: observe the page, take the single next in-scope action, then verify against the acceptance check. Keep only verified progress. Stop when the page url has changed from the login page to an authenticated resource, or on no measurable progress. Ask before any irreversible or out-of-scope action or any side-effecting browser action.

---
_Generated from `examples/login-flow/SKILL.md` (SHA-256 `4246b68b0b5a5cae…`) by
`integration/core/skill_to_loop.py`. This is a ForgeLoop adaptation of the Forge
skill into a Loopy-style loop — not a published Loop Library loop._
