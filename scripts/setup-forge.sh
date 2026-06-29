#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup-forge.sh — prepare Forge (recording + distillation) to run inside
# ForgeLoop.
#
#   1. Verify the Forge code is present in forge/.
#   2. Create forge/.env.local from forge/config.example.env (the file Forge
#      actually reads — server + harness + entry point).
#   3. Install the Python runtime deps (Forge runs on pure Python).
#   4. Build the Chrome extension if Node/pnpm is available (optional).
#
# Forge ("Journey Forge Local") is pure Python at runtime — the server and the
# distillation harness need no Node. Node/pnpm is only used to BUILD the
# recorder extension. Idempotent: safe to re-run.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- 1. Code present? -------------------------------------------------------
if [ ! -f forge/requirements.txt ] || [ ! -f forge/server/server.py ]; then
  echo "!! forge/ does not look like Browser-BC (missing requirements.txt or" >&2
  echo "   server/server.py). It is committed in-tree; if you removed it, run" >&2
  echo "   ./scripts/vendor.sh forge to refresh it from upstream." >&2
  exit 1
fi

# --- 2. forge/.env.local (Forge's own config) -------------------------------
# Prefer environment variables (Claude Code env / CI secrets) — no key in the repo.
if [ -n "${SF_LLM_KEY:-}" ]; then
  "$ROOT/scripts/write-env.sh"
elif [ ! -f forge/.env.local ]; then
  echo "==> Creating forge/.env.local from forge/config.example.env"
  cp forge/config.example.env forge/.env.local
  echo "    Set SF_LLM_KEY (env var, or edit forge/.env.local) before distilling."
fi

# ForgeLoop's own orchestration .env (ports, governance) — separate layer.
if [ ! -f .env ]; then
  echo "==> Creating .env from .env.example"
  cp .env.example .env
fi

# --- 3. Python runtime deps -------------------------------------------------
PY="${JFL_PYTHON:-python3}"
echo "==> [python] installing forge/requirements.txt with $PY"
"$PY" -m pip install -r forge/requirements.txt

# --- 4. Build the recorder extension (optional, needs Node/pnpm) ------------
if [ -f forge/extension/package.json ]; then
  if command -v pnpm >/dev/null 2>&1; then
    echo "==> [node] building recorder extension (pnpm)"
    ( cd forge/extension && pnpm install && pnpm build )
    echo "    Load unpacked: forge/extension/dist/chrome-mv3"
  else
    echo "!! pnpm not found — skipping extension build." >&2
    echo "   Install Node + pnpm, then: ( cd forge/extension && pnpm install && pnpm build )" >&2
  fi
fi

echo "==> Forge setup complete. See docs/forge-setup.md to record your first workflow."
