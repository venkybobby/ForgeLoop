#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# bootstrap.sh — one-shot local setup. forge/ and loopy/ are committed in-tree,
# so this just creates config and installs dependencies for both subsystems.
# (Run ./scripts/vendor.sh first only if you want to refresh upstream code.)
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "================ ForgeLoop bootstrap ================"

[ -f .env ] || { echo "==> Creating .env from .env.example"; cp .env.example .env; }

"$ROOT/scripts/setup-forge.sh"
"$ROOT/scripts/setup-loopy.sh"

echo "===================================================="
echo "Bootstrap complete."
echo "  Next: set SF_LLM_KEY in forge/.env.local, then follow docs/forge-setup.md"
