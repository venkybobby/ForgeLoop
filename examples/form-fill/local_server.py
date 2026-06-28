"""local_server — a faithful local copy of the httpbin.org/forms/post order form.

Public egress is blocked in the ForgeLoop sandbox, so live browser runs target a
local copy of the form instead of the real site. The HTML mirrors httpbin's form
(same field names) and the element XPaths match `trace.json`, so replaying the
recording drives this page exactly as it would the real one. POSTing to `/post`
returns a confirmation page that echoes the submitted fields — giving the loop
real result-page content to verify its acceptance criteria against.

Run standalone:   python examples/form-fill/local_server.py [port]
Or import serve() to start it in a background thread for a scripted run.
"""

from __future__ import annotations

import http.server
import socketserver
import threading
from urllib.parse import parse_qs

FORM_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Pizza Order (local httpbin copy)</title></head>
<body>
  <h1>Customer Order Form</h1>
  <form action="/post" method="post">
    <p><label>Customer name: <input name="custname"></label></p>
    <p><label>Telephone: <input type="tel" name="custtel"></label></p>
    <p><label>E-mail: <input type="email" name="custemail"></label></p>
    <fieldset>
      <legend>Pizza Size</legend>
      <label><input type="radio" name="size" value="small">Small</label>
      <label><input type="radio" name="size" value="medium">Medium</label>
      <label><input type="radio" name="size" value="large">Large</label>
    </fieldset>
    <fieldset>
      <legend>Pizza Toppings</legend>
      <label><input type="checkbox" name="topping" value="bacon">Bacon</label>
      <label><input type="checkbox" name="topping" value="cheese">Extra Cheese</label>
      <label><input type="checkbox" name="topping" value="onion">Onion</label>
    </fieldset>
    <p><label>Delivery instructions: <textarea name="comments"></textarea></label></p>
    <p><button type="submit">Submit order</button></p>
  </form>
</body></html>"""


def _result_html(fields: dict) -> str:
    rows = "".join(
        f"<tr><td>{k}</td><td>{', '.join(v)}</td></tr>" for k, v in sorted(fields.items())
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Order received</title></head>
<body>
  <h1 id="confirmation">Order received — thank you!</h1>
  <p id="status">Your order was submitted successfully.</p>
  <table id="echo">{rows}</table>
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
        if self.path.rstrip("/") in ("", "/forms/post", "/forms"):
            self._send(FORM_HTML)
        else:
            self._send("<h1>Not found</h1>", 404)

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n).decode("utf-8")
        fields = parse_qs(raw)
        self._send(_result_html(fields))


def serve(port: int = 0) -> tuple[socketserver.TCPServer, str]:
    """Start the server in a background thread; return (server, base_url)."""
    httpd = socketserver.TCPServer(("127.0.0.1", port), _Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


if __name__ == "__main__":
    import sys
    httpd, base = serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8011)
    print(f"serving the order form at {base}/forms/post  (Ctrl-C to stop)")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        httpd.shutdown()
