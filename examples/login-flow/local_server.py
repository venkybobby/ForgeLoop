"""local_server — a local copy of the-internet.herokuapp.com login form.

Public egress is blocked in the ForgeLoop sandbox, so live browser runs target a
local copy. The element ids (`username`, `password`) and the submit button match
`trace.json`, so replaying the recording drives this page exactly as it would the
real site. A correct login navigates to `/secure` and renders the secure-area
page; wrong credentials re-render the login form with an error — giving the loop
real result-page content to verify acceptance against.

Run standalone:   python examples/login-flow/local_server.py [port]
Or import serve() to start it in a background thread for a scripted run.
"""

from __future__ import annotations

import http.server
import socketserver
import threading
from urllib.parse import parse_qs

VALID = {"username": "tomsmith", "password": "SuperSecretPassword!"}  # public demo creds

LOGIN_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Login Page</title></head>
<body>
  <h2>Login Page</h2>
  {error}
  <form action="/secure" method="post">
    <label>Username <input type="text" name="username" id="username"></label>
    <label>Password <input type="password" name="password" id="password"></label>
    <button type="submit"><i class="fa fa-sign-in"></i> Login</button>
  </form>
</body></html>"""

SECURE_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Secure Area</title></head>
<body>
  <h2 id="secure">Secure Area</h2>
  <div id="flash" class="success">You logged into a secure area!</div>
  <p>Welcome to the Secure Area. When you are done click logout below.</p>
</body></html>"""


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _send(self, html: str, code: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path.rstrip("/") in ("", "/login"):
            self._send(LOGIN_HTML.format(error=""))
        elif self.path.rstrip("/") == "/secure":
            self._send(SECURE_HTML)
        else:
            self._send("<h1>Not found</h1>", 404)

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length", 0))
        fields = parse_qs(self.rfile.read(n).decode("utf-8"))
        ok = (fields.get("username", [""])[0] == VALID["username"]
              and fields.get("password", [""])[0] == VALID["password"])
        if ok:
            self._send(SECURE_HTML)
        else:
            err = '<div id="flash" class="error">Your username/password is invalid!</div>'
            self._send(LOGIN_HTML.format(error=err))


def serve(port: int = 0) -> tuple[socketserver.TCPServer, str]:
    httpd = socketserver.TCPServer(("127.0.0.1", port), _Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


if __name__ == "__main__":
    import sys
    httpd, base = serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8012)
    print(f"serving the login form at {base}/login  (Ctrl-C to stop)")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        httpd.shutdown()
