#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup-loopy.sh — prepare Loopy (loop library + agent skills) inside ForgeLoop.
#
# Loopy is primarily a library of loops + agent skills (Markdown/skill files,
# no runtime install needed). The only installable piece is the optional
# Cloudflare worker under loopy/loop-library/worker (Node). Idempotent.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- Code present? ----------------------------------------------------------
if [ ! -d loopy/skills ] || [ ! -d loopy/loop-library ]; then
  echo "!! loopy/ does not look like the loopy repo (missing skills/ or" >&2
  echo "   loop-library/). It is committed in-tree; run ./scripts/vendor.sh loopy" >&2
  echo "   to refresh it from upstream if you removed it." >&2
  exit 1
fi

[ -f .env ] || { echo "==> Creating .env from .env.example"; cp .env.example .env; }

# --- Optional: build the loop-library worker (Node) -------------------------
WORKER="loopy/loop-library/worker"
if [ -f "$WORKER/package.json" ]; then
  if command -v pnpm >/dev/null 2>&1 || command -v npm >/dev/null 2>&1; then
    echo "==> [node] installing $WORKER"
    ( cd "$WORKER" && { command -v pnpm >/dev/null 2>&1 && pnpm install || npm install; } )
  else
    echo "!! Node not found — skipping optional worker install ($WORKER)." >&2
  fi
fi

echo "==> Loopy setup complete."
echo "    The agent-facing Loopy skill lives in loopy/skills/loopy/. See docs/loopy-setup.md."
