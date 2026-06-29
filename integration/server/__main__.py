"""python -m integration.server [host] [port]  — run the ForgeLoop web app."""

from __future__ import annotations

import os
import sys

from .app import serve

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(sys.argv[2]) if len(sys.argv) > 2 else int(os.environ.get("DASHBOARD_PORT", "8055"))
    serve(host, port)
