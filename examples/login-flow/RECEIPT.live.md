## Loopy run receipt

Loop: Login with Credentials Loop
Definition: local loop.md SHA-256 a540c6289c74d29c…; trace=trace.json; boundary=recorded plan length (safety backstop 25)
Scope: herokuapp.com (LIVE browser run) via http://127.0.0.1:57607
Check: URL leaves the form page AND the result page renders; acceptance: “The page URL has changed from the login page to an authenticated resource”
Boundary: recorded plan length (safety backstop 25)
Result: Success
Timestamp: 2026-06-29T00:12:15.594533+00:00

Evidence:
- Acceptance criteria: 5.
- Replaying 6 recorded step(s) against a live page (host rewritten to http://127.0.0.1:57607).
- Governance: 5 red line(s); approval granted.
- Form URL: http://127.0.0.1:57607/login
- Final URL: http://127.0.0.1:57607/secure  (changed: yes)
- Result page text (extracted): “Secure Area You logged into a secure area! Welcome to the Secure Area. When you are done click logout below.”
- Screenshot: /home/user/forgeloop/examples/login-flow/evidence/result.png

Actions:
- Pass 1: navigated → http://127.0.0.1:57607/login
- Pass 2: click username
- Pass 3: fill username
- Pass 4: click password
- Pass 5: fill password
- Pass 6: click Login

Next: nothing — acceptance met on the live page.
