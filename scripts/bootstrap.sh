#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# bootstrap.sh — one-shot local setup: vendor upstream code, create .env,
# install dependencies for both Forge and Loopy.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "================ ForgeLoop bootstrap ================"

"$ROOT/scripts/vendor.sh" all

[ -f .env ] || { echo "==> Creating .env from .env.example"; cp .env.example .env; }

"$ROOT/scripts/setup-forge.sh"
"$ROOT/scripts/setup-loopy.sh"

echo "===================================================="
echo "Bootstrap complete."
echo "  Next: edit .env (set ANTHROPIC_API_KEY), then follow docs/forge-setup.md"
