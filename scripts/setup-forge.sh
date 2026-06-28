#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup-forge.sh — prepare Forge (recording + distillation) to run inside
# ForgeLoop.
#
#   1. Verify forge/ has been vendored.
#   2. Ensure .env exists (copy from .env.example if not).
#   3. Install dependencies for each Forge subsystem that is present.
#
# Idempotent: safe to re-run. Detects Node (package.json) and Python
# (requirements.txt / pyproject.toml) projects automatically.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- 1. Vendored? -----------------------------------------------------------
if [ -z "$(find forge -mindepth 1 -maxdepth 1 ! -name README.md 2>/dev/null)" ]; then
  echo "!! forge/ is empty. Run ./scripts/vendor.sh first." >&2
  exit 1
fi

# --- 2. .env ----------------------------------------------------------------
if [ ! -f .env ]; then
  echo "==> Creating .env from .env.example"
  cp .env.example .env
  echo "    Edit .env and set ANTHROPIC_API_KEY before distilling."
fi

# --- 3. Install deps per subsystem ------------------------------------------
install_node() {
  local dir="$1"
  [ -f "$dir/package.json" ] || return 0
  echo "==> [node] installing in $dir"
  ( cd "$dir" && { command -v pnpm >/dev/null && pnpm install || npm install; } )
}

install_python() {
  local dir="$1"
  if [ -f "$dir/requirements.txt" ]; then
    echo "==> [python] installing $dir/requirements.txt"
    ( cd "$dir" && python3 -m pip install -r requirements.txt )
  elif [ -f "$dir/pyproject.toml" ]; then
    echo "==> [python] installing $dir (pyproject)"
    ( cd "$dir" && python3 -m pip install -e . )
  fi
}

for sub in forge/server forge/harness forge/app forge/extension; do
  [ -d "$sub" ] || continue
  install_node "$sub"
  install_python "$sub"
done

echo "==> Forge setup complete. See docs/forge-setup.md to record your first workflow."
