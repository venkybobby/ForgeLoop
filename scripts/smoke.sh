#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# smoke.sh — fast, dependency-light checks for CI and local use.
#
# No network, no LLM, no browser: syntax-checks the shell + Python, then exercises
# the non-browser flow (bind -> simulate -> catalog -> dashboard) so a broken
# import or CLI regression fails the build. Browser/agentic paths are covered by
# the demo scripts, not here (they need Playwright/Chromium + egress).
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> shell syntax (bash -n)"
for s in scripts/*.sh; do bash -n "$s"; done

echo "==> python syntax (py_compile: integration + scripts)"
python3 -m py_compile $(find integration scripts -name '*.py')

echo "==> functional smoke (no network/browser)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export FORGELOOP_DB="$tmp/forgeloop.db"   # isolate the SQLite store for CI

python3 -m integration.cli.forgeloop bind examples/form-fill/SKILL.md --out "$tmp/loop.md" >/dev/null
python3 -m integration.cli.forgeloop run "$tmp/loop.md" --skill examples/form-fill/SKILL.md --simulate >/dev/null
python3 -m integration.cli.forgeloop catalog >/dev/null
python3 -m integration.dashboard.build --out "$tmp/dash.html" >/dev/null

# token-gate sanity: a gated server returns 401 without a token, 200 on /healthz.
FORGELOOP_TOKEN=ci-smoke python3 -m integration.server 127.0.0.1 8099 >/tmp/smoke-srv.log 2>&1 &
srv=$!
for _ in $(seq 1 20); do curl -sf -o /dev/null http://127.0.0.1:8099/healthz && break || sleep 0.3; done
code_health=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8099/healthz)
code_gated=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8099/api/catalog)
kill "$srv" 2>/dev/null || true
[ "$code_health" = "200" ] || { echo "!! /healthz expected 200, got $code_health" >&2; exit 1; }
[ "$code_gated" = "401" ] || { echo "!! gated /api/catalog expected 401, got $code_gated" >&2; exit 1; }

echo "smoke OK"
